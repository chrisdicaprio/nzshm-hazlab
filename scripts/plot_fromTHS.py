import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from nzshm_common.location.location import LOCATIONS_BY_ID
from nzshm_common.location.code_location import CodedLocation
from nzshm_common.grids.region_grid import load_grid
from toshi_hazard_store.query_v3 import get_hazard_curves


from oq_hazard_report.plotting_functions import plot_hazard_curve_fromdf

ARCHIVE_DIR = '/home/chrisdc/NSHM/oqdata/HAZ_CURVE_ARCHIVE'

def get_hazard(hazard_id, locs, vs30, imts, aggs, force=False):

    curves_filename = f'{hazard_id}-{vs30}.json'
    curves_filepath = Path(ARCHIVE_DIR,curves_filename)

    if curves_filepath.exists() and (not force):
        dtype = {'lat':str,'lon':str}
        hazard_data = pd.read_json(curves_filepath,dtype=dtype)
        return hazard_data

    columns = ['lat', 'lon', 'imt', 'agg', 'level', 'hazard']
    index = range(len(locs) * len(imts) * len(aggs) * 29)
    hazard_curves = pd.DataFrame(columns=columns, index=index)

    ind = 0
    for i,res in enumerate(get_hazard_curves(locs, [vs30], [hazard_id], imts, aggs)):
        lat = f'{res.lat:0.3f}'
        lon = f'{res.lon:0.3f}'
        for value in res.values:
            hazard_curves.loc[ind,'lat'] = lat
            hazard_curves.loc[ind,'lon'] = lon
            hazard_curves.loc[ind,'imt'] = res.imt
            hazard_curves.loc[ind,'agg'] = res.agg
            hazard_curves.loc[ind,'level'] = value.lvl
            hazard_curves.loc[ind,'hazard'] = value.val
            ind += 1

    hazard_curves.to_json(curves_filepath)
    return hazard_curves




# ███╗░░░███╗░█████╗░██╗███╗░░██╗
# ████╗░████║██╔══██╗██║████╗░██║
# ██╔████╔██║███████║██║██╔██╗██║
# ██║╚██╔╝██║██╔══██║██║██║╚████║
# ██║░╚═╝░██║██║░░██║██║██║░╚███║
# ╚═╝░░░░░╚═╝╚═╝░░╚═╝╚═╝╚═╝░░╚══╝

plot_title = 'SLT v8, GMCM v2'
fig_dir = Path('/home/chrisdc/NSHM/oqresults/Full_Models/SLT_v8_gmm_v2/tmp2')
# /home/chrisdc/NSHM/oqresults/Full_Models/SLT_v6_gmm_v0b/Compare/GMCM_corr')
hazard_models = [
    # dict(id='SLT_v8_gmm_v1',name='SLT v8, GMCM EE'),
    dict(id='SLT_v8_gmm_v2',name='SLT v8, GMCM v2'),
    dict(id='SLT_v8_gmm_v2_TEST2',name='SLT v8, TEST'),
]

legend = True
vs30 = 400
# vs30 = 750
# imts = ['PGA', 'SA(0.1)', 'SA(0.2)', 'SA(0.3)', 'SA(0.4)', 'SA(0.5)', 'SA(0.7)','SA(1.0)', 'SA(1.5)', 'SA(2.0)', 'SA(3.0)', 'SA(4.0)', 'SA(5.0)', 'SA(6.0)','SA(7.5)', 'SA(10.0)']
imts = ['PGA','SA(0.5)', 'SA(1.5)', 'SA(3.0)']
aggs = ["mean", "0.005", "0.01", "0.025", "0.05", "0.1", "0.2", "0.5", "0.8", "0.9", "0.95", "0.975", "0.99", "0.995"]


locations = [f"{loc['latitude']:0.3f}~{loc['longitude']:0.3f}" for loc in LOCATIONS_BY_ID.values()] 

xscale = 'log'
xlim = [1e-2,1e1]
# xlim = [0,3]
ylim = [1e-6,1]
# ylim = [0,.0025]


#=============================================================================================================================#



PLOT_WIDTH = 12
PLOT_HEIGHT = 8.625
grid_res = 0.001
colors = ['#1b9e77', '#d95f02', '#7570b3']

if not fig_dir.exists():
    fig_dir.mkdir()

for hazard_model in hazard_models:
    hazard_model['data'] = get_hazard(hazard_model['id'], locations, vs30, imts, aggs)

POES = [0.1,0.02]
INVESTIGATION_TIME = 50
bandws = {
            # '0.5,10,90,99.5':{'lower2':'0.005','lower1':'0.1','upper1':'0.9','upper2':'0.995'},
            '10,20,80,90':{'lower2':'0.01','lower1':'0.1','upper1':'0.9','upper2':'0.99'},
        }

ref_lines = []
for poe in POES:
        ref_line = dict(type = 'poe',
                        poe = poe,
                        inv_time = INVESTIGATION_TIME)
        ref_lines.append(ref_line)

for imt in imts:
    for location in LOCATIONS_BY_ID.keys():
        if location != "WLG":
            continue
        print(f'plotting {location} ... ')
        for bounds,bandw in bandws.items():
            pt = (LOCATIONS_BY_ID[location]["latitude"], LOCATIONS_BY_ID[location]["longitude"])
            loc = CodedLocation(*pt,grid_res).downsample(grid_res).code
            name = LOCATIONS_BY_ID[location]['name']

            fig, ax = plt.subplots(1,1)
            fig.set_size_inches(PLOT_WIDTH,PLOT_HEIGHT)
            fig.set_facecolor('white')

            handles = []
            labels = []
            for i, hazard_model in enumerate(hazard_models):
                handles.append(
                    plot_hazard_curve_fromdf(hazard_model['data'], loc, imt, ax, xlim, ylim,
                                                xscale=xscale,central='mean',
                                                bandw=bandw,ref_lines=ref_lines,
                                                color=colors[i]))
                labels.append(hazard_model['name'])


            if legend:
                plt.legend(handles,labels)
            title = f'{plot_title} {name} vs30={vs30} {imt} {bounds}'
            plot_name = '_'.join( (name,str(vs30),imt,bounds) ) + '.png'
            file_path = Path(fig_dir,plot_name) 
            ax.set_title(title)
            # plt.savefig(file_path)
            plt.show()
            plt.close()
