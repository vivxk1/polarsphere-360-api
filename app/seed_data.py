"""The demo universe shared by every page of the frontend.

Stations, the 43rd ISEA expedition, 16 documents, 12 datasets and 10 media items
with polar-science content realistic enough that RAG answers are grounded in
something plausible. Replace with real NCPOR material whenever available.
"""

STATIONS = [
    {
        "id": "maitri",
        "name": "Maitri",
        "region": "Antarctica",
        "station_type": "Inland research station",
        "established": 1989,
        "lat": -70.7669,
        "lon": 11.7339,
        "summary": (
            "India's second permanent Antarctic station, located in the Schirmacher Oasis, "
            "roughly 100 km inland from the coast. Maitri supports atmospheric sciences, "
            "low-temperature biology, geomagnetism and glaciology, and serves as the inland "
            "logistics hub for expeditions into the ice sheet."
        ),
        "meta": {
            "iceThickness": "~100 m (over rock)",
            "summerPopulation": 65,
            "winterPopulation": 25,
            "nearestCoast": "~100 km",
        },
    },
    {
        "id": "bharati",
        "name": "Bharati",
        "region": "Antarctica",
        "station_type": "Coastal research station",
        "established": 2012,
        "lat": -69.4064,
        "lon": 76.1917,
        "summary": (
            "India's third Antarctic station, built on the Larsemann Hills of Prydz Bay. "
            "Bharati is a coastal station focused on oceanography, sea-ice physics, marine "
            "biology and geodesy, with a modern container-based design that can host 72 "
            "researchers in summer."
        ),
        "meta": {
            "commissioned": "2012",
            "summerPopulation": 72,
            "focus": ["Oceanography", "Sea ice", "Marine biology", "Geodesy"],
        },
    },
    {
        "id": "himadri",
        "name": "Himadri",
        "region": "Arctic",
        "station_type": "Arctic research station",
        "established": 2008,
        "lat": 78.9227,
        "lon": 11.9273,
        "summary": (
            "India's first Arctic research station, situated at Ny-Alesund in the Svalbard "
            "archipelago. Himadri studies Arctic atmospheric processes, glacier mass balance, "
            "permafrost dynamics, and the coupling between Arctic and monsoon systems."
        ),
        "meta": {
            "host": "Ny-Alesund, Svalbard",
            "focus": ["Atmospheric science", "Glaciology", "Permafrost", "Monsoon coupling"],
        },
    },
]

EXPEDITION = {
    "id": "43rd-isea",
    "name": "43rd Indian Scientific Expedition to Antarctica",
    "season": "2023-2024",
    "status": "completed",
    "start_date": "2023-11-15",
    "end_date": "2024-03-20",
    "lead_institution": "NCPOR",
    "summary": (
        "The 43rd ISEA carried 47 members to Maitri and Bharati with a science programme "
        "spanning atmospheric chemistry, sea-ice mass balance, ice-shelf monitoring, marine "
        "biodiversity and geodesy. The expedition also completed the annual re-supply of "
        "Maitri and validated a new autonomous weather station network across Prydz Bay."
    ),
}

EXPEDITION_EVENTS = [
    {"date": "2023-11-15", "title": "Departure from Goa", "kind": "logistics",
     "description": "Expedition members sailed aboard the charter vessel with 480 tonnes of cargo and fuel."},
    {"date": "2023-12-02", "title": "Arrival at Prydz Bay", "kind": "logistics",
     "description": "Fast ice edge reached; Bharati re-supply began via ice-track vehicles."},
    {"date": "2023-12-18", "title": "Bharati science programme begins", "kind": "science",
     "description": "Oceanographic CTD casts and sea-ice mass balance stakes installed on Prydz Bay fast ice."},
    {"date": "2024-01-06", "title": "Maitri inland traverse", "kind": "logistics",
     "description": "Convoy reached Schirmacher Oasis after a five-day traverse from the coast."},
    {"date": "2024-01-22", "title": "Autonomous weather network live", "kind": "science",
     "description": "Six AWS nodes around Larsemann Hills started streaming to the NCPOR data centre."},
    {"date": "2024-02-11", "title": "Ice-shelf survey completed", "kind": "science",
     "description": "Ground-penetrating radar and GNSS surveys mapped ice-shelf thinning over 42 km."},
    {"date": "2024-03-05", "title": "Marine biodiversity sampling", "kind": "science",
     "description": "Benthic and plankton samples collected from 18 stations for molecular analysis."},
    {"date": "2024-03-20", "title": "Expedition return", "kind": "logistics",
     "description": "Team and equipment returned; science cargo and samples transferred to NCPOR."},
]

EXPEDITION_MEMBERS = [
    {"name": "Dr. A. Sharma", "role": "Expedition Leader", "organisation": "NCPOR", "is_lead": True},
    {"name": "Dr. R. Iyer", "role": "Atmospheric Scientist", "organisation": "NCPOR"},
    {"name": "Dr. M. Kulkarni", "role": "Sea Ice Physicist", "organisation": "IIT Bombay"},
    {"name": "S. Nair", "role": "Glaciologist", "organisation": "NCPOR"},
    {"name": "Dr. P. Ghosh", "role": "Marine Biologist", "organisation": "CMLRE"},
    {"name": "V. Reddy", "role": "Geodesy Engineer", "organisation": "NCPOR"},
    {"name": "Dr. K. Menon", "role": "Medical Officer", "organisation": "NCPOR"},
    {"name": "J. Fernandes", "role": "Station Engineer", "organisation": "NCPOR"},
    {"name": "Dr. T. Bose", "role": "Oceanographer", "organisation": "INCOIS"},
    {"name": "A. Pillai", "role": "Field Assistant", "organisation": "NCPOR"},
]

THEME_LABELS = {
    "sea-ice": "Sea Ice",
    "atmospheric": "Atmospheric Science",
    "glaciology": "Glaciology",
    "oceanography": "Oceanography",
    "geophysics": "Geophysics",
    "biology": "Biology",
    "permafrost": "Permafrost",
    "geology": "Geology",
    "remote-sensing": "Remote Sensing",
    "climate": "Climate",
}

DOCUMENTS = [
    {
        "title": "Sea Ice Mass Balance Observations, Prydz Bay 2023-24",
        "doc_type": "report",
        "station_id": "bharati",
        "theme": "sea-ice",
        "year": 2024,
        "abstract": "Seasonal evolution of landfast sea ice measured with an ablation stake network.",
        "body": (
            "During the 43rd Indian Scientific Expedition to Antarctica, a network of 24 ablation "
            "stakes was installed on the landfast sea ice of Prydz Bay adjacent to Bharati. Stakes "
            "were surveyed every five days from early December 2023 until late February 2024. "
            "Maximum consolidated ice thickness reached 1.62 m in mid-January, with a mean snow "
            "depth of 0.21 m over the ice surface.\n\n"
            "Surface ablation dominated from mid-December onwards, removing on average 0.34 m of "
            "ice, while basal growth contributed 0.48 m over the same period. The net seasonal mass "
            "balance was therefore slightly positive at most sites. Snow depth proved to be the "
            "strongest control on thickness: sites with more than 0.3 m of snow showed markedly "
            "reduced basal growth because of insulation.\n\n"
            "Sea ice in Prydz Bay formed later and broke out earlier than the 2015-2020 mean. "
            "Breakout occurred on 18 February 2024 following a sustained warm advection event, "
            "roughly nine days earlier than the climatological average. These observations are "
            "consistent with a shortening landfast ice season in East Antarctica."
        ),
    },
    {
        "title": "Aerosol Optical Depth and Black Carbon at Maitri",
        "doc_type": "paper",
        "station_id": "maitri",
        "theme": "atmospheric",
        "year": 2024,
        "abstract": "Continuous measurements of aerosol optical depth and equivalent black carbon.",
        "body": (
            "A microtops sunphotometer and an aethalometer were operated at Maitri throughout the "
            "2023-24 austral summer. Aerosol optical depth at 500 nm averaged 0.048, among the "
            "lowest recorded values for any continental site, confirming the exceptionally clean "
            "background atmosphere of the Schirmacher Oasis.\n\n"
            "Equivalent black carbon concentrations averaged 118 ng per cubic metre, with episodic "
            "peaks up to 420 ng per cubic metre associated with long-range transport from southern "
            "Africa and South America. Back-trajectory analysis attributed 68 percent of these "
            "episodes to biomass burning plumes arriving after five to seven days of transport.\n\n"
            "Because the Antarctic atmosphere is so clean, even small amounts of light-absorbing "
            "aerosol produce a measurable radiative effect. The estimated direct radiative forcing "
            "from black carbon at Maitri during the observation window was between 0.08 and "
            "0.19 watts per square metre."
        ),
    },
    {
        "title": "Ice Shelf Thinning Near the Larsemann Hills",
        "doc_type": "report",
        "station_id": "bharati",
        "theme": "glaciology",
        "year": 2024,
        "abstract": "Ground-penetrating radar and GNSS survey of ice-shelf thickness change.",
        "body": (
            "A combined ground-penetrating radar and GNSS survey was conducted over 42 km of the "
            "ice shelf north of the Larsemann Hills in February 2024. Radar was collected at 400 MHz "
            "along eleven transverse profiles, and positions were recorded with dual-frequency GNSS "
            "for precise elevation control.\n\n"
            "Comparison with the 2018 survey shows mean thinning of 1.9 m over the six-year interval, "
            "equivalent to 0.32 m per year. Thinning is not uniform: the eastern sector thinned at "
            "0.61 m per year while the central sector thinned at only 0.11 m per year. The pattern "
            "correlates with the location of basal channels visible in satellite imagery.\n\n"
            "Basal melting, rather than surface processes, accounts for most of the loss. Surface "
            "mass balance over the same period was near neutral, with summer melt largely offset by "
            "snow accumulation. The survey will be repeated annually to track the evolution of the "
            "basal channel system."
        ),
    },
    {
        "title": "CTD Hydrography of Prydz Bay",
        "doc_type": "dataset-documentation",
        "station_id": "bharati",
        "theme": "oceanography",
        "year": 2024,
        "abstract": "Conductivity-temperature-depth profiles from 31 stations in Prydz Bay.",
        "body": (
            "Thirty-one conductivity-temperature-depth casts were completed in Prydz Bay between "
            "December 2023 and February 2024. Profiles extend from the surface to within 10 m of the "
            "seabed, with a maximum cast depth of 1,180 m.\n\n"
            "Three water masses were identified. Antarctic Surface Water occupies the upper 100 m "
            "with temperatures between -1.8 and 0.4 degrees Celsius. Circumpolar Deep Water is "
            "present between 400 and 900 m and is consistently warmer than 0.6 degrees Celsius, "
            "making it the primary source of oceanic heat available to melt the ice shelf. "
            "Antarctic Bottom Water appears below 1,000 m with potential temperature below "
            "-0.5 degrees Celsius.\n\n"
            "The thermocline depth shoaled by approximately 40 m relative to the 2019 occupation, "
            "which increases the heat flux reaching the ice-shelf cavity. Repeat hydrography is "
            "planned annually to determine whether this shoaling is a trend or interannual "
            "variability."
        ),
    },
    {
        "title": "Geomagnetic Observatory Report, Maitri",
        "doc_type": "report",
        "station_id": "maitri",
        "theme": "geophysics",
        "year": 2023,
        "abstract": "Annual summary of geomagnetic field observations and disturbance statistics.",
        "body": (
            "The geomagnetic observatory at Maitri recorded continuous three-component field data "
            "throughout 2023 with 99.4 percent data availability. Absolute observations were made "
            "weekly using a fluxgate theodolite to control baseline drift.\n\n"
            "The station lies close to the southern auroral zone, so it records large substorm "
            "signatures. Forty-one storms with a disturbance storm time index below minus 50 "
            "nanotesla were recorded during the year, the strongest reaching minus 148 nanotesla in "
            "late April.\n\n"
            "Secular variation at Maitri continues to show a westward drift of the magnetic field "
            "at roughly 0.14 degrees per year in declination. Data are transmitted to the "
            "international geomagnetic data centre and contribute to global field models."
        ),
    },
    {
        "title": "Marine Benthic Biodiversity of Prydz Bay",
        "doc_type": "paper",
        "station_id": "bharati",
        "theme": "biology",
        "year": 2024,
        "abstract": "Benthic community composition from 18 stations, with molecular barcoding.",
        "body": (
            "Benthic samples were collected with a van Veen grab from 18 stations at depths between "
            "30 and 620 m in Prydz Bay during February 2024. Specimens were sorted, photographed "
            "and sequenced for cytochrome c oxidase subunit I barcodes.\n\n"
            "One hundred and forty-two operational taxonomic units were identified. Polychaetes and "
            "crustaceans dominated shallow stations, while echinoderms and sponges were more "
            "abundant below 300 m. Twelve sequences did not match any reference above 97 percent "
            "identity and may represent undescribed taxa.\n\n"
            "Community composition showed a strong depth gradient and a weaker relationship with "
            "sediment grain size. Two stations close to the ice-shelf front had markedly lower "
            "abundance, consistent with disturbance from iceberg scouring."
        ),
    },
    {
        "title": "Permafrost Thermal State at Ny-Alesund",
        "doc_type": "report",
        "station_id": "himadri",
        "theme": "permafrost",
        "year": 2023,
        "abstract": "Borehole temperature monitoring of Arctic permafrost near Himadri.",
        "body": (
            "Six boreholes between 10 and 30 m deep were instrumented with thermistor strings near "
            "Himadri in Ny-Alesund. Temperatures are logged hourly and transmitted via satellite.\n\n"
            "Mean annual ground temperature at 10 m depth ranged from minus 2.9 to minus 1.4 degrees "
            "Celsius across the sites. Active layer thickness at the end of the 2023 thaw season "
            "ranged from 0.86 to 1.42 m, exceeding the 2015-2020 mean by roughly 0.13 m.\n\n"
            "The warmest site is adjacent to a retreating glacier margin, where thin sediment cover "
            "and recent exposure amplify warming. Thawing permafrost releases previously frozen "
            "organic carbon, and dissolved organic carbon concentrations in nearby runoff have "
            "increased by 22 percent since monitoring began."
        ),
    },
    {
        "title": "Glacier Mass Balance, Svalbard",
        "doc_type": "report",
        "station_id": "himadri",
        "theme": "glaciology",
        "year": 2023,
        "abstract": "Annual mass balance for two monitored Arctic glaciers.",
        "body": (
            "Two glaciers near Ny-Alesund were monitored using the glaciological method, with "
            "ablation stakes and snow pits measured in April and September. Both glaciers have "
            "continuous records extending back to 2009.\n\n"
            "The 2023 net mass balance was minus 0.71 m water equivalent for the larger glacier and "
            "minus 0.94 m water equivalent for the smaller one. Both values are more negative than "
            "the long-term mean of minus 0.48 m water equivalent.\n\n"
            "The equilibrium line altitude rose by about 90 m compared with the 2009-2018 mean, "
            "leaving a larger fraction of each glacier in the ablation zone. At current rates the "
            "smaller glacier is projected to lose most of its accumulation area within four decades."
        ),
    },
    {
        "title": "Geology of the Schirmacher Oasis",
        "doc_type": "report",
        "station_id": "maitri",
        "theme": "geology",
        "year": 2022,
        "abstract": "Bedrock mapping and geochronology of the Schirmacher Oasis.",
        "body": (
            "The Schirmacher Oasis exposes a granulite-facies basement of charnockite, "
            "enderbite and garnet-biotite gneiss along an 18 km coastal strip. New field mapping "
            "and zircon geochronology were completed over two seasons.\n\n"
            "Uranium-lead zircon ages cluster at 550 to 530 million years, corresponding to the "
            "Pan-African orogeny and confirming correlation with the East African Orogen. A later "
            "thermal overprint at roughly 500 million years is recorded in metamorphic rims.\n\n"
            "Glacial striations and erratics across the oasis record ice flow from the south-east, "
            "consistent with thickening of the East Antarctic Ice Sheet during glacial maxima. "
            "The oasis has remained ice free for at least the last several hundred thousand years."
        ),
    },
    {
        "title": "Satellite Derived Sea Ice Concentration, East Antarctica",
        "doc_type": "dataset-documentation",
        "station_id": "bharati",
        "theme": "remote-sensing",
        "year": 2024,
        "abstract": "Passive microwave sea ice concentration validated against in situ observations.",
        "body": (
            "Daily sea ice concentration from passive microwave brightness temperature was compared "
            "with in situ observations and ship-based visual estimates around Prydz Bay for the "
            "2023-24 season.\n\n"
            "Overall agreement was good during mid-winter, with a root mean square difference of "
            "6.4 percent. Agreement degraded during melt and freeze-up, when the difference "
            "exceeded 15 percent because surface meltwater alters the microwave signature.\n\n"
            "The satellite record indicates that sea ice extent around East Antarctica reached a "
            "record low in February 2023, followed by a near-average maximum in September 2023. "
            "This large swing within a single year highlights the importance of maintaining "
            "continuous in situ validation."
        ),
    },
    {
        "title": "Autonomous Weather Station Network, Larsemann Hills",
        "doc_type": "report",
        "station_id": "bharati",
        "theme": "atmospheric",
        "year": 2024,
        "abstract": "Deployment and first season of a six node AWS network.",
        "body": (
            "Six autonomous weather stations were installed across the Larsemann Hills and adjacent "
            "fast ice in January 2024. Each station measures air temperature, relative humidity, "
            "wind speed and direction, pressure, and snow depth, and transmits hourly via Iridium.\n\n"
            "First-season data availability was 94 percent, with losses mainly caused by rime "
            "accretion on anemometers at exposed sites. The network resolves a persistent "
            "katabatic flow from the interior that is not captured by the single station at Bharati.\n\n"
            "Temperature differences between the coastal and inland nodes exceeded 9 degrees Celsius "
            "on calm clear days, demonstrating strong local variability. The network will be "
            "extended in future seasons to better constrain the surface energy budget."
        ),
    },
    {
        "title": "Trace Gas Measurements at Bharati",
        "doc_type": "paper",
        "station_id": "bharati",
        "theme": "atmospheric",
        "year": 2023,
        "abstract": "Carbon dioxide and methane time series from a coastal Antarctic site.",
        "body": (
            "A cavity ring-down spectrometer measured carbon dioxide and methane at Bharati from "
            "February 2022 to November 2023. Calibration was performed monthly against two "
            "reference gas cylinders traceable to the international scale.\n\n"
            "Carbon dioxide showed a clear seasonal cycle with a peak-to-trough amplitude of "
            "1.9 parts per million, with the minimum in late austral summer. The mean growth rate "
            "was 2.4 parts per million per year, consistent with the global background.\n\n"
            "Methane averaged 1,782 parts per billion and grew by 9.4 parts per billion per year. "
            "Short-lived excursions above the baseline were traced to local emissions from station "
            "operations and were excluded from the trend analysis."
        ),
    },
    {
        "title": "Bathymetric Survey of the Prydz Bay Shelf",
        "doc_type": "dataset-documentation",
        "station_id": "bharati",
        "theme": "oceanography",
        "year": 2023,
        "abstract": "Multibeam bathymetry gridded at 25 m for 340 square kilometres.",
        "body": (
            "Multibeam bathymetry was collected over 340 square kilometres of the Prydz Bay "
            "continental shelf and gridded at 25 m resolution. Soundings were corrected for sound "
            "velocity profiles and tidal variation.\n\n"
            "The survey reveals a deep trough crossing the shelf, reaching 1,180 m, that channels "
            "warm Circumpolar Deep Water toward the ice-shelf front. Iceberg plough marks are "
            "abundant on the shallow banks at depths between 120 and 260 m.\n\n"
            "The gridded product improves on previous regional compilations by roughly an order of "
            "magnitude in resolution and will be used to constrain circulation models of the "
            "ice-shelf cavity."
        ),
    },
    {
        "title": "Microbial Diversity in Antarctic Soils",
        "doc_type": "paper",
        "station_id": "maitri",
        "theme": "biology",
        "year": 2023,
        "abstract": "Metagenomic survey of soil microbial communities in the Schirmacher Oasis.",
        "body": (
            "Soil samples from twelve sites across the Schirmacher Oasis were sequenced using "
            "shotgun metagenomics. Sites ranged from nutrient-poor mineral soils to ornithogenic "
            "soils beneath penguin colonies.\n\n"
            "Bacterial community composition was strongly structured by nutrient availability. "
            "Actinobacteria and Acidobacteria dominated oligotrophic sites, while ornithogenic "
            "soils were enriched in Firmicutes and Bacteroidetes. Archaeal reads were rare at all "
            "sites.\n\n"
            "Functional gene analysis identified cold-adapted enzymes including cold-active "
            "lipases and cellulases, which are of interest for biotechnology. Several recovered "
            "genomes represent lineages with no close cultivated relatives."
        ),
    },
    {
        "title": "Geodetic Infrastructure and Crustal Motion at Bharati",
        "doc_type": "report",
        "station_id": "bharati",
        "theme": "geophysics",
        "year": 2024,
        "abstract": "Continuous GNSS and superconducting gravimeter operations.",
        "body": (
            "Bharati hosts a continuously operating GNSS station and, since 2021, a "
            "superconducting gravimeter. Both contribute to international geodetic networks.\n\n"
            "The GNSS solution gives vertical uplift of 4.1 mm per year and horizontal motion of "
            "12.6 mm per year, consistent with regional glacial isostatic adjustment models for "
            "Prydz Bay following deglaciation.\n\n"
            "The gravimeter records Earth tides, ocean tidal loading and hydrological signals. "
            "After removing these, a residual gravity trend indicates ongoing mass redistribution "
            "associated with contemporary ice loss in the catchment."
        ),
    },
    {
        "title": "Arctic-Monsoon Teleconnection Study",
        "doc_type": "paper",
        "station_id": "himadri",
        "theme": "climate",
        "year": 2023,
        "abstract": "Statistical links between Arctic sea ice and the Indian summer monsoon.",
        "body": (
            "This study examines the statistical relationship between spring Arctic sea ice "
            "concentration and subsequent Indian summer monsoon rainfall, using reanalysis and "
            "rain gauge records from 1979 to 2022.\n\n"
            "A significant negative correlation is found between May sea ice concentration in the "
            "Barents-Kara sector and monsoon rainfall over central India, with a correlation "
            "coefficient of minus 0.42. Low spring sea ice tends to precede weaker monsoon "
            "rainfall.\n\n"
            "The proposed mechanism involves altered meridional temperature gradients that shift "
            "the position of the subtropical jet and delay monsoon onset. The relationship is "
            "statistically significant but explains only part of monsoon variance, so it should be "
            "used as one predictor among several."
        ),
    },
]

DATASETS = [
    {"title": "Maitri Air Temperature (hourly)", "station_id": "maitri", "theme": "atmospheric",
     "year": 2024, "format": "CSV", "variables": ["air_temperature"], "unit": "degC", "rows": 8760,
     "size_label": "1.2 MB", "abstract": "Hourly air temperature at 2 m from the Maitri AWS.", "span": "annual"},
    {"title": "Bharati Sea Ice Thickness (5-day)", "station_id": "bharati", "theme": "sea-ice",
     "year": 2024, "format": "CSV", "variables": ["ice_thickness", "snow_depth"], "unit": "m", "rows": 520,
     "size_label": "84 KB", "abstract": "Ablation stake network measurements of landfast ice.", "span": "seasonal"},
    {"title": "Prydz Bay CTD Profiles", "station_id": "bharati", "theme": "oceanography",
     "year": 2024, "format": "NetCDF", "variables": ["temperature", "salinity", "pressure"], "unit": "mixed", "rows": 31,
     "size_label": "46 MB", "abstract": "31 full-depth hydrographic casts.", "span": "seasonal"},
    {"title": "Maitri Aerosol Optical Depth", "station_id": "maitri", "theme": "atmospheric",
     "year": 2024, "format": "CSV", "variables": ["aod_500nm"], "unit": "dimensionless", "rows": 2140,
     "size_label": "310 KB", "abstract": "Sunphotometer aerosol optical depth at 500 nm.", "span": "seasonal"},
    {"title": "Bharati Trace Gas Time Series", "station_id": "bharati", "theme": "atmospheric",
     "year": 2023, "format": "CSV", "variables": ["co2", "ch4"], "unit": "ppm/ppb", "rows": 15840,
     "size_label": "2.4 MB", "abstract": "Carbon dioxide and methane from cavity ring-down spectroscopy.", "span": "annual"},
    {"title": "Ny-Alesund Permafrost Temperatures", "station_id": "himadri", "theme": "permafrost",
     "year": 2023, "format": "CSV", "variables": ["ground_temperature"], "unit": "degC", "rows": 52560,
     "size_label": "6.1 MB", "abstract": "Hourly borehole thermistor data from six boreholes.", "span": "annual"},
    {"title": "Maitri Geomagnetic Field (1-min)", "station_id": "maitri", "theme": "geophysics",
     "year": 2023, "format": "CSV", "variables": ["h_component", "d_component", "z_component"], "unit": "nT", "rows": 525600,
     "size_label": "38 MB", "abstract": "Three-component geomagnetic field observations.", "span": "annual"},
    {"title": "Larsemann Hills AWS Network", "station_id": "bharati", "theme": "atmospheric",
     "year": 2024, "format": "CSV", "variables": ["air_temperature", "wind_speed"], "unit": "mixed", "rows": 41000,
     "size_label": "5.5 MB", "abstract": "Six autonomous weather stations, hourly telemetry.", "span": "seasonal"},
    {"title": "Satellite Sea Ice Concentration (daily)", "station_id": "bharati", "theme": "remote-sensing",
     "year": 2024, "format": "NetCDF", "variables": ["ice_concentration"], "unit": "percent", "rows": 365,
     "size_label": "112 MB", "abstract": "Passive microwave sea ice concentration, 25 km grid.", "span": "annual"},
    {"title": "Prydz Bay Multibeam Bathymetry", "station_id": "bharati", "theme": "oceanography",
     "year": 2023, "format": "NetCDF", "variables": ["depth"], "unit": "m", "rows": 544000,
     "size_label": "88 MB", "abstract": "Bathymetry gridded at 25 m over 340 square kilometres.", "span": "static"},
    {"title": "Svalbard Glacier Mass Balance", "station_id": "himadri", "theme": "glaciology",
     "year": 2023, "format": "CSV", "variables": ["net_balance", "ela"], "unit": "m w.e.", "rows": 28,
     "size_label": "12 KB", "abstract": "Annual mass balance for two monitored glaciers since 2009.", "span": "decadal"},
    {"title": "Schirmacher Soil Metagenomes", "station_id": "maitri", "theme": "biology",
     "year": 2023, "format": "FASTQ", "variables": ["read_count"], "unit": "reads", "rows": 14400000,
     "size_label": "4.2 GB", "abstract": "Shotgun metagenomic sequencing of twelve soil samples.", "span": "static"},
]

MEDIA = [
    {"title": "Maitri station at midnight sun", "media_type": "image", "station_id": "maitri",
     "theme": "station-life", "year": 2024, "tags": ["station", "summer"],
     "transcript": "Panoramic photograph of Maitri under continuous daylight in January."},
    {"title": "Sea ice breakout timelapse, Prydz Bay", "media_type": "video", "station_id": "bharati",
     "theme": "sea-ice", "year": 2024, "tags": ["breakout", "timelapse"],
     "transcript": "Timelapse covering 72 hours of landfast ice breakout in mid February."},
    {"title": "Aurora australis over Bharati", "media_type": "video", "station_id": "bharati",
     "theme": "geophysics", "year": 2024, "tags": ["aurora", "night"],
     "transcript": "Wide field footage of a substorm aurora with green and red emission bands."},
    {"title": "Emperor penguin colony census", "media_type": "image", "station_id": "maitri",
     "theme": "biology", "year": 2023, "tags": ["wildlife", "census"],
     "transcript": "Aerial oblique image used for colony count estimation."},
    {"title": "Ice core drilling, Schirmacher", "media_type": "image", "station_id": "maitri",
     "theme": "glaciology", "year": 2023, "tags": ["ice-core", "fieldwork"],
     "transcript": "Researchers handling a 42 m firn core segment on a drilling platform."},
    {"title": "CTD cast deployment", "media_type": "video", "station_id": "bharati",
     "theme": "oceanography", "year": 2024, "tags": ["ctd", "ship"],
     "transcript": "Deck footage of a rosette sampler being lowered through a hydrohole."},
    {"title": "Katabatic winds soundscape", "media_type": "audio", "station_id": "maitri",
     "theme": "atmospheric", "year": 2024, "tags": ["soundscape", "wind"],
     "transcript": "Two minute recording of sustained katabatic wind at 18 metres per second."},
    {"title": "Himadri station in polar night", "media_type": "image", "station_id": "himadri",
     "theme": "station-life", "year": 2023, "tags": ["station", "arctic"],
     "transcript": "Himadri illuminated against the Ny-Alesund polar night sky."},
    {"title": "Traverse convoy to Maitri", "media_type": "image", "station_id": "maitri",
     "theme": "logistics", "year": 2024, "tags": ["traverse", "vehicles"],
     "transcript": "Tracked vehicle convoy on the inland traverse route from the coast."},
    {"title": "Benthic sample sorting", "media_type": "image", "station_id": "bharati",
     "theme": "biology", "year": 2024, "tags": ["laboratory", "benthos"],
     "transcript": "Laboratory image of sorted benthic invertebrates in petri dishes."},
]

MAP_LAYERS = [
    {
        "layer": "stations",
        "properties": {"name": "Maitri", "kind": "station"},
        "geometry": {"type": "Point", "coordinates": [11.7339, -70.7669]},
    },
    {
        "layer": "stations",
        "properties": {"name": "Bharati", "kind": "station"},
        "geometry": {"type": "Point", "coordinates": [76.1917, -69.4064]},
    },
    {
        "layer": "stations",
        "properties": {"name": "Himadri", "kind": "station"},
        "geometry": {"type": "Point", "coordinates": [11.9273, 78.9227]},
    },
    {
        "layer": "expedition-route",
        "properties": {"name": "43rd ISEA voyage", "vessel": "chartered ice-class vessel"},
        "geometry": {
            "type": "LineString",
            "coordinates": [[73.9, 15.3], [57.5, -20.2], [30.0, -45.0], [11.73, -70.77]],
        },
    },
    {
        "layer": "expedition-route",
        "properties": {"name": "Inland traverse to Maitri", "kind": "over-ice"},
        "geometry": {
            "type": "LineString",
            "coordinates": [[11.2, -69.9], [11.4, -70.2], [11.6, -70.5], [11.7339, -70.7669]],
        },
    },
    {
        "layer": "sea-ice",
        "properties": {"name": "Prydz Bay landfast ice", "season": "2023-24", "maxThickness": "1.62 m"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[75.8, -69.2], [76.6, -69.2], [76.6, -69.7], [75.8, -69.7], [75.8, -69.2]]],
        },
    },
]
