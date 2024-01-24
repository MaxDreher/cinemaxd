import requests

def get_awards_and_nominations(wikidata_id):
    # Wikidata API endpoint
    wikidata_api_url = f'https://www.wikidata.org/w/api.php'

    # Parameters for the API request
    params = {
        'action': 'wbgetentities',
        'ids': wikidata_id,
        'format': 'json',
        'props': 'claims',  # Include claims (statements) in the response
    }

    # Make the API request
    response = requests.get(wikidata_api_url, params=params)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        data = response.json()
        # Extract statements from the response
        entity = data.get('entities', {}).get(wikidata_id, {})
        claims = entity.get('claims', {})

        # Print "award received" statements
        awards_statements = claims.get('P166', [])
        print('Award Received:')
        for statement in awards_statements:
            mainsnak = statement.get('mainsnak', {})
            datavalue = mainsnak.get('datavalue', {})
            value = datavalue.get('value')
            print(f'  Statement ID: {statement.get("id")}, Value: {value}')

        # Print "nominated for" statements
        nominations_statements = claims.get('P1411', [])
        print('Nominated For:')
        for statement in nominations_statements:
            mainsnak = statement.get('mainsnak', {})
            datavalue = mainsnak.get('datavalue', {})
            value = datavalue.get('value')
            print(f'  Statement ID: {statement.get("id")}, Value: {value}')

    else:
        print(f'Error: Unable to fetch data from Wikidata API. Status Code: {response.status_code}')

# Example usage with a Wikidata ID
wikidata_id = 'Q20856802'  # Example ID for "The Shawshank Redemption"
get_awards_and_nominations(wikidata_id)
