# Results Tables - Nutrition/Anaemia/Child-Health Determinants, Ghana 261 Districts

## Table 1. Characteristics of the 261 districts of Ghana, 2022

| Characteristic                           | Mean (SD)   | Median [IQR]     | Range     |
|:-----------------------------------------|:------------|:-----------------|:----------|
| Poverty incidence (%)                    | 27.6 (13.4) | 25.8 [17.6-36.0] | 6.3-68.6  |
| Poverty intensity (%)                    | 43.4 (1.7)  | 43.1 [42.2-44.3] | 40.5-51.2 |
| Illiteracy rate (%)                      | 29.0 (14.7) | 26.9 [17.9-40.5] | 5.4-60.8  |
| NHIS-uninsured share (%)                 | 30.9 (13.5) | 30.2 [20.3-40.7] | 5.2-73.2  |
| Employment rate (%)                      | 49.3 (8.2)  | 50.7 [46.6-54.7] | 15.5-64.0 |
| Under-15 population share (%)            | 35.9 (4.9)  | 35.9 [33.7-37.8] | 19.0-49.6 |
| Improved water (%, region)               | 89.1 (10.3) | 91.8 [88.4-96.8] | 59.3-98.5 |
| Improved sanitation (%, region)          | 64.5 (21.8) | 72.0 [51.7-84.7] | 21.9-91.4 |
| Stunting - district posterior (%)        | 16.4 (5.6)  | 16.0 [11.9-18.4] | 7.5-34.6  |
| Anaemia - district posterior (%)         | 48.1 (11.7) | 45.1 [38.9-55.1] | 30.5-74.4 |
| IYCF inadequacy - district posterior (%) | 76.2 (6.6)  | 75.8 [72.2-79.5] | 58.5-91.8 |
| Diarrhoea - district posterior (%)       | 14.6 (6.2)  | 12.7 [9.6-19.2]  | 4.2-34.1  |


## Table 2. Global and local spatial autocorrelation (BYM2 posterior surfaces)

| Outcome         |   Moran's I (queen) |    z |     p |   Moran's I (KNN5) | LISA HH / LL   | Gi* hot / cold   |
|:----------------|--------------------:|-----:|------:|-------------------:|:---------------|:-----------------|
| Stunting        |               0.937 | 23.3 | 0.002 |              0.851 | 27 / 44        | 41 / 51          |
| Anaemia         |               0.959 | 23.2 | 0.002 |              0.909 | 51 / 54        | 61 / 62          |
| IYCF inadequacy |               0.836 | 20.8 | 0.002 |              0.829 | 31 / 22        | 43 / 42          |
| Diarrhoea       |               0.821 | 19.8 | 0.002 |              0.694 | 30 / 20        | 62 / 45          |


## Table 3. SHAP determinant importance - top 5 per outcome (XGBoost exact TreeSHAP, 40x bootstrap)

| Outcome         |   Rank | Determinant          |   Mean |SHAP| | 95% bootstrap CI   |   Stability SD |   Stability (CV) |
|:----------------|-------:|:---------------------|--------------:|:-------------------|---------------:|-----------------:|
| Stunting        |      1 | Under-15 share       |         2.318 | 1.851-2.799        |          0.257 |             0.11 |
| Stunting        |      2 | Improved water       |         1.249 | 0.999-1.627        |          0.162 |             0.13 |
| Stunting        |      3 | Improved sanitation  |         0.758 | 0.436-1.235        |          0.214 |             0.28 |
| Stunting        |      4 | Poverty intensity    |         0.312 | 0.216-0.453        |          0.076 |             0.24 |
| Stunting        |      5 | Poverty incidence    |         0.256 | 0.084-0.675        |          0.143 |             0.56 |
| Anaemia         |      1 | Improved sanitation  |         5.504 | 4.794-6.300        |          0.406 |             0.07 |
| Anaemia         |      2 | Illiteracy rate      |         2.849 | 2.033-3.645        |          0.414 |             0.14 |
| Anaemia         |      3 | Poverty incidence    |         1.335 | 0.759-1.825        |          0.285 |             0.21 |
| Anaemia         |      4 | Poverty intensity    |         1.183 | 0.930-1.478        |          0.174 |             0.15 |
| Anaemia         |      5 | Under-15 share       |         0.805 | 0.557-1.075        |          0.137 |             0.17 |
| IYCF inadequacy |      1 | Improved water       |         1.619 | 1.064-2.454        |          0.375 |             0.23 |
| IYCF inadequacy |      2 | Poverty intensity    |         1.581 | 1.266-1.851        |          0.172 |             0.11 |
| IYCF inadequacy |      3 | Under-15 share       |         1.558 | 1.134-1.953        |          0.247 |             0.16 |
| IYCF inadequacy |      4 | Illiteracy rate      |         1.308 | 0.989-1.726        |          0.231 |             0.18 |
| IYCF inadequacy |      5 | Improved sanitation  |         0.713 | 0.480-0.967        |          0.15  |             0.21 |
| Diarrhoea       |      1 | Under-15 share       |         2.728 | 2.375-3.136        |          0.206 |             0.08 |
| Diarrhoea       |      2 | Improved sanitation  |         1.958 | 1.619-2.286        |          0.2   |             0.1  |
| Diarrhoea       |      3 | Improved water       |         0.993 | 0.721-1.270        |          0.163 |             0.16 |
| Diarrhoea       |      4 | NHIS-uninsured share |         0.916 | 0.609-1.204        |          0.152 |             0.17 |
| Diarrhoea       |      5 | Urbanicity           |         0.404 | 0.183-0.629        |          0.135 |             0.34 |


## Table 4. Small-area, GWR and machine-learning model summary

| Outcome         |   phi (spatial fraction) |   Hotspots P>0.95 |   GWR dAICc | GWR non-stationary   |   XGB LOROCV R2 |   RF LOROCV R2 |   Hotspot AUC-PR |
|:----------------|-------------------------:|------------------:|------------:|:---------------------|----------------:|---------------:|-----------------:|
| Stunting        |                     0.37 |                31 |         321 | Yes                  |            0.38 |           0.43 |            0.773 |
| Anaemia         |                     0.35 |                60 |         368 | Yes                  |            0.82 |           0.76 |            0.947 |
| IYCF inadequacy |                     0.37 |                37 |         249 | Yes                  |           -0.07 |          -0.15 |            0.417 |
| Diarrhoea       |                     0.35 |                51 |         225 | Yes                  |           -0.06 |           0.2  |            0.476 |


## Table 5. Confirmed quadruple-burden hotspot districts (P>0.95 for all four outcomes; n = 17)

| District                | Region   |   Stunting % |   Anaemia % |   IYCF inadeq % |   Diarrhoea % |
|:------------------------|:---------|-------------:|------------:|----------------:|--------------:|
| Gushegu Municipal       | Northern |        34.58 |       72.69 |           84.85 |         26.75 |
| Karaga                  | Northern |        33.63 |       74.41 |           84.2  |         25.88 |
| Kpandai                 | Northern |        26.3  |       67.06 |           89.01 |         27.93 |
| Kumbungu                | Northern |        32.1  |       73.35 |           85.24 |         25.07 |
| Mion                    | Northern |        31.89 |       72.54 |           88.6  |         28.43 |
| Nanton                  | Northern |        31.61 |       72.33 |           86.51 |         25.31 |
| Nanumba North Municipal | Northern |        29.88 |       67.98 |           90.15 |         28.06 |
| Nanumba South           | Northern |        30.22 |       69.25 |           90.33 |         31.46 |
| Saboba                  | Northern |        29.78 |       69.3  |           85.83 |         23.37 |
| Savelugu Municipal      | Northern |        31.76 |       72.08 |           84.98 |         22.62 |
| Tatale Sanguli          | Northern |        30.92 |       70.68 |           88.86 |         28.67 |
| Tolon                   | Northern |        30.44 |       72.81 |           85.2  |         24.2  |
| Yendi Municipal         | Northern |        30.03 |       69.21 |           86.24 |         21.65 |
| Zabzugu                 | Northern |        31.41 |       70.47 |           89.2  |         28.46 |
| Central Gonja           | Savannah |        23.89 |       66.54 |           89.55 |         28.66 |
| North East Gonja        | Savannah |        24.86 |       67.04 |           90.86 |         32.4  |
| North Gonja             | Savannah |        24.69 |       68.26 |           89.73 |         30.56 |
