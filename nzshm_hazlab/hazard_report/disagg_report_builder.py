import numpy as np
from pathlib import Path, PurePath

import markdown
from markdown.extensions.toc import TocExtension

import matplotlib.pyplot as plt

import nzshm_hazlab.disagg_plotting_functions as dpf
import nzshm_hazlab.disagg_data_functions as ddf
from nzshm_hazlab.hazard_report.resources.css_template import disagg_css_file as css_file

HEAD_HTML = '''
<!DOCTYPE html>
<html>
<head>
<title>##TITLE##</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="disagg_report.css">
<style>
    .markdown-body {
        box-sizing: border-box;
        min-width: 200px;
        max-width: 1000px;
        margin: 0 auto;
        padding: 45px;
    }

    @media (max-width: 767px) {
        .markdown-body {
            padding: 15px;
        }
    }
</style>
</head>
<article class="markdown-body">

'''

TAIL_HTML = '''
</article>
</html>

'''


class DisaggReportBuilder:

    def __init__(self, name, shaking_level, disagg_data, bins, output_path):

        self._name = name
        self._output_path = Path(output_path)
        self._shaking_level = shaking_level

        self._disagg = disagg_data
        self._bins = bins

        if self._output_path.exists() and (not self._output_path.is_dir()):
            raise Exception(f'output path {self._output_path} is not a directory')
        
        if not self._output_path.exists():
            self._output_path.mkdir()


    def load_data(self):
        pass
        # self._disagg = np.load(self._data_filepath)
        # self._bins = np.load(self._bins_filepath, allow_pickle=True)

    
    def run(self):

        self._plot_dir = Path(self._output_path, 'figures')
        if not self._plot_dir.is_dir():
            self._plot_dir.mkdir()

        self._data_dir = Path(self._output_path, 'data')
        if not self._data_dir.is_dir():
            self._data_dir.mkdir()

        self.load_data()

        tables = [] 
        tables.append(self.generate_mean_table())
        tables.append(self.generate_mode_table(['mag','dist']))
        tables.append(self.generate_mode_table(['mag','dist','eps']))
        plots = self.generate_plots()

        self.generate_report(tables, plots)
        self.generate_csv()

    def generate_csv(self):

        header = f'{self._name}, {self._shaking_level:.2e}g '
        bins = {'magnitude':0, 'distance':1, 'epsilon':3}
        for k,v in bins.items():
            bin_edges = [1.5*self._bins[v][0] - 0.5*self._bins[v][1], ]
            for b in self._bins[v]:
                bin_edges.append( b - bin_edges[-1] + b )
            header += f'{k} bin edges = {bin_edges} '

        csv_filepath = Path(self._data_dir, 'disagg.csv')
        ddf.disagg_to_csv(self._disagg, self._bins, header, csv_filepath)

    
    def generate_mode_table(self, dimensions):

        dims = dict(
            dist = 'Distance',
            mag = 'Magnitude',
            eps = 'Epsilon',
            trt = 'Tectonic Region Type',
        )
        mode, contribution = ddf.calc_mode_disagg(self._disagg, self._bins, dimensions)
        table = {'type':'flat'}
        table['title'] = 'Mode (' + ' '.join(dimensions) + ')'
        table['rows'] = []
        for d in dimensions:
            table['rows'].append([dims[d] + ':', f'{mode[d]:0.1f}'])
        table['rows'].append(['Contribution:', f'{contribution*100:0.2f}%'])
        return table 

    
    def generate_mean_table(self):

        means = ddf.calc_mean_disagg(self._disagg, self._bins)
        table = {'type':'flat'}
        table['title'] = 'Mean Source'
        table['rows'] = [ 
                ['Distance:', f'{int(means["dist"])}', 'km'], 
                ['Magnitude:', f'{means["mag"]:0.1f}'],
                ['Epsilon:', f'{means["eps"]:0.1f}', '&sigma;'],
        ]

        return table 


    def generate_plots(self):

        plots = []

        plots.append( dict(
                    level=1,
                    text='Tectonic Region Type',
                    figs=[])
                )
        text = 'This bar chart shows the relative contributions to hazard from each tectonic region'
        plots.append(dict(level=0, text=text))
        plots += self.make_trt_plot()

        plots.append(dict(level='hrule'))

        plots.append( dict(
            level=1,
            text='Magnitude-Distance',
            figs=[])
        )
        text = 'This plot shows the contribution to hazard by distance to source and event magnitude.'
        plots.append(dict(level=0, text=text))
        plots += self.make_mag_dist_plot()

        plots.append(dict(level='hrule'))

        plots.append( dict(
                    level=1,
                    text='Magnitude-Distance-TRT',
                    figs=[])
                )
        text = 'This plot shows the contribution to hazard by distance to source and event magnitude for each tectonic region.\
            This can be used to determine what type of events contribute most to the seismic hazard.'
        plots.append(dict(level=0, text=text))
        plots += self.make_mag_dist_trt_plot()

        plots.append(dict(level='hrule'))

        plots.append( dict(
                    level=1,
                    text='Magnitude-Distance-Epsilon',
                    figs=[])
                )
        text = 'This plot shows the contribution to hazard by distance to source and event magnitude colored by epsilon.\
            Epsilon is the number of standard deviations by which the (logarithmic) acceleration differs\
                 from the mean (logarithmic) acceleration of a ground-motion prediction equation. \
                 The two plots differ only in the maximum distance plotted.'
        plots.append(dict(level=0, text=text))
        plots += self.make_mag_dist_eps_plot()


        return plots


    def make_trt_plot(self):
        
        fig, ax = plt.subplots(1,1)
        fig.set_size_inches(7,5)    
        fig.set_facecolor('white')
        plot_path = PurePath(self._plot_dir,'trt_bar.png')
        plot_rel_path = PurePath(plot_path.parent.name, plot_path.name)

        dpf.plot_trt(fig, ax, self._disagg, self._bins)
        plt.savefig(str(plot_path), bbox_inches="tight")
        plt.close(fig)

        plots = [
            dict(
            level=4,
            text='',
            fig = plot_rel_path
            )
        ]

        return plots


    def make_mag_dist_plot(self):
        
        fig, ax = plt.subplots(1,1)
        fig.set_size_inches(8,6)    
        fig.set_facecolor('white')
        plot_path = PurePath(self._plot_dir,'mag_dist_2d.png')
        plot_rel_path = PurePath(plot_path.parent.name,plot_path.name)

        dpf.plot_mag_dist_2d(fig, ax, self._disagg, self._bins)
        plt.savefig(str(plot_path), bbox_inches="tight")
        plt.close(fig)

        plots = [
            dict(
            level=4,
            text='',
            fig = plot_rel_path
            )
        ]

        return plots

    def make_mag_dist_trt_plot(self):
        
        fig, ax = plt.subplots(1,3)
        fig.set_size_inches(12,3)    
        fig.set_facecolor('white')
        plot_path = PurePath(self._plot_dir,'mag_dist_trt_2d.png')
        plot_rel_path = PurePath(plot_path.parent.name,plot_path.name)

        dpf.plot_mag_dist_trt_2d(fig, ax, self._disagg, self._bins)
        plt.savefig(str(plot_path), bbox_inches="tight")
        plt.close(fig)

        plots = [
            dict(
            level=4,
            text='',
            fig = plot_rel_path
            )
        ]

        return plots

    def make_mag_dist_eps_plot(self):

        ymaxma = [100,350]
        fig_table = [[]]
        for ymax in ymaxma:

            fig = plt.figure()
            fig.set_size_inches(8,8)
            fig.set_facecolor('white')
            plot_path = PurePath(self._plot_dir,f'mag_dist_eps_{ymax}.png')
            plot_rel_path = PurePath(plot_path.parent.name,plot_path.name)
            dpf.plot_mag_dist_eps(fig, self._disagg, self._bins, ylim = (0,ymax), min_mag_bin_width=0.3)
            plt.savefig(str(plot_path), bbox_inches="tight")
            plt.close(fig)
            fig_table[0].append(plot_rel_path)


        title_table = [['_','_']]

        plots = [
            dict(
            level=4,
            text='',
            # fig = plot_rel_path
            fig_table = {'figs':fig_table,'titles':title_table}
            )
        ]

        return plots


    def generate_report(self, tables, plots):

        print('generating report . . .')
        md_string = f'# {self._name}\n'
        gm = f'{self._shaking_level:.2e}'.split('e')
        gm[1] = gm[1][0] + gm[1][2:] if gm[1][1] == '0' else gm[1]
        md_string += f'## Ground Motion: {gm[0]} x 10' + f'<sup>{gm[1]}</sup>g\n'

        md_string += '---\n'

        for table in tables:
            md_string += '\n## ' + table['title'] + '\n'
            if table['type'] == 'flat':
                for row in table['rows']:
                    md_string += '**' + row[0] + '** '
                    md_string += ' '.join(row[1:]) + '  \n'
            else:
                md_string += '| ' + ' | '.join(table['header'])  + ' |\n'
                md_string += '| ' + '|'.join([' ---- ']*len(table['header'])) + ' |\n'
                for row in table['rows']:
                    md_string += '| ' + ' | '.join(row) + ' |\n '

        md_string += '\n---\n' 
        for plot in plots:
            if plot["level"] == 'hrule':
                md_string += '\n---\n'
            elif plot["level"] == 0:
                md_string += plot["text"] + '\n'
            else:
                md_string += f'{"#"*(plot["level"]+1)} {plot["text"]}\n'
            # if plot['level'] < 4:
            #     md_string += f'[top](#top)\n'
            if plot.get('fig'):
                md_string += f'<a href={plot["fig"]} target="_blank">![an image]({plot["fig"]})</a>\n'
            if plot.get('fig_table'):
                md_string += self.build_fig_table(plot.get('fig_table'))
        
    
        # html = markdown.markdown(md_string, extensions=[TocExtension(toc_depth="2-4"),'tables'])
        html = markdown.markdown(md_string,extensions=['tables'])

        head_html = HEAD_HTML.replace('##TITLE##',self._name)
        html = head_html + html + TAIL_HTML        
        
        with open(PurePath(self._output_path, 'index.html'),'w') as output_file:
            output_file.write(html)

        with open(PurePath(self._output_path, 'disagg_report.css'),'w') as output_file:
            output_file.write(css_file)

        print('done generating report')


    def build_fig_table(self,fig_table):

        #TODO error handling for titles and figs not same shape

        def end_row(table_md):
            return table_md[:-3] + '\n'
        
        def insert_header_break(table_md,ncols):
            for col in range(ncols):
                table_md += ': ------------- : | '
            return table_md

        figs = fig_table.get('figs')
        titles = fig_table.get('titles')

        nrows = len(figs)
        ncols = len(figs[0])
        ncols_header = ncols

        table_md = '\n'

        for row in range(nrows):
            ncols = len(figs[row])

            for col in range(ncols):
                table_md += f'{titles[row][col]} | '
                if ncols < ncols_header:
                    for i in range(ncols_header-ncols):
                        table_md += '. | '
            table_md = end_row(table_md)

            if row==0:
                table_md = insert_header_break(table_md,ncols)
                table_md = end_row(table_md)

            for col in range(ncols):
                fig = figs[row][col]
                table_md += f'<a href={fig} target="_blank">![an image]({fig})<a href={fig} target="_blank"> | '
                if ncols < ncols_header:
                    for i in range(ncols_header-ncols):
                        table_md += '. | '

            table_md = end_row(table_md)

        table_md += '\n'

        return table_md        
