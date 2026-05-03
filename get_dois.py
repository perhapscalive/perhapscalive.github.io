import urllib.request, urllib.parse, json

titles = [
    "Multi-model analysis of historical runoff changes in the Lancang-Mekong River Basin¨CCharacteristics and uncertainties",
    "Synergistic impact of complex topography and climate variability on the loss of microclimate heterogeneity in Southeast Asia",
    "Clustering the diurnal cycle of precipitation using global satellite data",
    "Impacts of moisture transport on extreme precipitation in the central plains urban agglomeration, China",
    "Anomalous water vapor circulation in an extreme drought event of the mid©\reaches of the Lancang©\Mekong River basin",
    "Changes in China's snow droughts characteristics from 1993 to 2019",
    "Regional changes of tropical cyclone rainfall in the western North Pacific"
]

for title in titles:
    url = f"https://api.crossref.org/works?query.title={urllib.parse.quote(title)}&select=DOI&rows=1"
    req = urllib.request.Request(url, headers={'User-Agent': 'mailto:test@example.com'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            items = data['message']['items']
            if items:
                print(f"DOI: {items[0].get('DOI', 'None')}")
            else:
                print("DOI: None")
    except Exception as e:
        print(f"Error: {e}")
