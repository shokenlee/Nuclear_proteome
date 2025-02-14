# Nuclear envelope proteome curated

Human proteome list of nuclear envelope (NE) was curated. See [Lee et al. 2024 bioRxiv](https://www.biorxiv.org/content/10.1101/2024.11.14.623600v2).

## File Structure

Pre-process the protein lists in '5 papers' and Human Protein Atlas
- `Schirmer2003.ipynb`: [Schirmer et al. 2003](https://doi.org/10.1126/science.1088176)
- `Korfali2010.ipynb`: [Korfali et al. 2010](https://doi.org/10.1074/mcp.m110.002915)
- `Korfali2012.ipynb`: [Korfali et al. 2012](https://doi.org/10.4161/nucl.22257)
- `Wilkie2010.ipynb`: [Wilkie et al. 2010](https://doi.org/10.1074/mcp.m110.003129)
- `Cheng2019.ipynb`: [Cheng et al. 2019](https://doi.org/10.26508/lsa.202301998)
- `HumanProteinAtlas.ipynb`: "Nuclear" proteins extracted from Human Protein Atlas in [Thul et al. 2017](https://doi.org/10.1126/science.aal3321)

Merge the lists and incorporating UniProt subcellular location information
- `MergingNEProteome.ipynb`: Merged the 5 lists from the NE proteome studies, resulting in 410 proteins
- `MergingNEProteome-HPA.ipynb`: Appended Human Protein Atlas information to the 410 NE proteins
- `Proteomics-HPA_UP-Subcell-retriev.ipynb`: Retrived UniProt subcellular location information for the 410 NE proteins
- `Proteomics-HPA_UP_Subcell_judge.ipynb`: Evaluate if the UniProt subcellular location information is reliable and not redundant with the NE proteome papers

Prioritize NE proteins supported by multiple NE proteome studies or by a single NE proteome study AND HPA or UniProt
- `NuclearProteome_Sum.ipynb`

Modules and config
- `my_utils.py`: Modules for API
- `my_config.py`: Configs for API



