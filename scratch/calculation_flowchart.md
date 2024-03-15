<style>
  .cluster-label span {
    display: block;
    margin-right: 120px;
    margin-left: 10px;
    margin-top: 1px;
  }
</style>
```mermaid
---
title: Processing flow diagram
---
%%{ init: { 'flowchart': { 'curve': 'basis' } } }%%
flowchart LR
    classDef node fill: #d6eaf8 , stroke:gray,stroke-width:2px;
    classDef box fill:white, stroke:black,stroke-width:2px;
    classDef box2 fill:white, stroke:gray,stroke-width:2px;
    classDef doc fill:#ffcfc4;

    %%S0([Approach])    
    %%S1([Logic Tree Formation])
    %%S2([Calculate Realizations])
    %%S3([Calculate Aggregate Statistics])

    Trad0[[Standard Approach]]

    Trad1["`**S1**. Form complete SLT from all combinations of the fault system logic tree branches`"]:::box

    Trad2["`**S2**. Combine complete SLT with GLT including all tectonic region types`"]:::box

    Trad3["`**S3**. Calculate all realizations of the complete logic tree`"]:::box

    Trad4["`**S4**. Calculate aggregate statistics from the weighted ensemble of all realizations`"]:::box

    New0[[New Approach]]

    New1["`**N1**. Combine each branch of each fault system SLT with the appropriate GLT for the tectonic region`"]:::box

    New2["`**N2**. Calculate realizations for each branch in step N1`"]:::box

    New3["`**N3**. Sum realizations to create all composite realizations of the complete logic tree`"]:::box

    New4["`**N4**. Calculate aggregate statistics from the weighted ensemble of all realizations`"]:::box

    %% links
    %%S0 ~~~ S1 ~~~~ S2 ~~~~ S3
    Trad0 ~~~ Trad1 ==> Trad2 ==> Trad3 ===> Trad4
    New0 ~~~ New1 ===> New2 ==> New3 ==> New4
    %%N1 ===> N2 ==> New3
```