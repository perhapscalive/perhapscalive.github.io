$titles = @(
    "Multi-model analysis of historical runoff changes in the Lancang-Mekong River Basin¨CCharacteristics and uncertainties",
    "Synergistic impact of complex topography and climate variability on the loss of microclimate heterogeneity in Southeast Asia",
    "Clustering the diurnal cycle of precipitation using global satellite data",
    "Impacts of moisture transport on extreme precipitation in the central plains urban agglomeration, China",
    "Anomalous water vapor circulation in an extreme drought event of the mid-reaches of the Lancang-Mekong River basin",
    "Changes in China's snow droughts characteristics from 1993 to 2019",
    "Regional changes of tropical cyclone rainfall in the western North Pacific"
)
foreach ($title in $titles) {
    try {
        $encodedTitle = [uri]::EscapeDataString($title)
        $url = "https://api.crossref.org/works?query.title=$encodedTitle&select=DOI&rows=1"
        $headers = @{"User-Agent"="mailto:hello@example.com"}
        $response = Invoke-RestMethod -Uri $url -Headers $headers
        if ($response.message.items.Count -gt 0) { Write-Host $response.message.items[0].DOI } else { Write-Host "None" }
    } catch {
        Write-Host "Error"
    }
}
