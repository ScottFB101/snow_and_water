from trafilatura import fetch_url, extract

# grab a HTML file to extract data from
downloaded = fetch_url(
    "https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-skills#creating-and-adding-a-skill"
)

# output main content and comments as plain text
result = extract(downloaded)
print(result)
