import requests
import xml.etree.ElementTree as ET
import csv
import time

# Function to perform the third API call
def get_site_details(site_id):
    # API endpoint for the third call
    site_api_url = f"https://api.acma.gov.au/SpectrumLicensingAPIOuterService/OuterService.svc/SiteSearchXML/{site_id}?searchField=SITE_ID"
    site_details = []
    
    try:
        # Making a GET request to the API for site details
        site_response = requests.get(site_api_url, timeout=10)
        
        if site_response.status_code == 200:
            # Parse the XML response
            site_root = ET.fromstring(site_response.content)
            # Assuming there's only one site per SITE_ID
            site = site_root.find('.//Site')
            if site is not None:
                long_name = site.find('LONG_NAME').text if site.find('LONG_NAME') is not None else 'N/A'
                city = site.find('CITY').text if site.find('CITY') is not None else 'N/A'
                postcode = site.find('POSTCODE').text if site.find('POSTCODE') is not None else 'N/A'
                state = site.find('STATE').text if site.find('STATE') is not None else 'N/A'
                latitude = site.find('LATITUDE').text if site.find('LATITUDE') is not None else 'N/A'
                longitude = site.find('LONGITUDE').text if site.find('LONGITUDE') is not None else 'N/A'
                details_url = site.find('DETAILS_URL').text if site.find('DETAILS_URL') is not None else 'N/A'
                site_details = [long_name, city, postcode, state, latitude, longitude, details_url]
        else:
            print(f"Failed to retrieve site details for {site_id}: HTTP Status Code", site_response.status_code)
    except requests.exceptions.RequestException as e:
        print(f"Request failed for {site_id}:", e)
    
    return site_details

# Function to perform the second API call
def get_registration_details(licence_no):
    # API endpoint for the second call
    registration_api_url = f"https://api.acma.gov.au/SpectrumLicensingAPIOuterService/OuterService.svc/RegistrationSearchXML?searchText={licence_no}&searchField=LICENCE_NO"
    registration_details = []
    
    try:
        # Making a GET request to the API for registration details
        registration_response = requests.get(registration_api_url, timeout=10)
        
        if registration_response.status_code == 200:
            # Parse the XML response
            registration_root = ET.fromstring(registration_response.content)
            # Loop over each Registration element
            for registration in registration_root.findall('.//Registration'):
                freq = registration.find('FREQ').text if registration.find('FREQ') is not None else 'N/A'
                device_type_text = registration.find('DEVICE_TYPE_TEXT').text if registration.find('DEVICE_TYPE_TEXT') is not None else 'N/A'
                emission_desig = registration.find('EMISSION_DESIG').text if registration.find('EMISSION_DESIG') is not None else 'N/A'
                site_id = registration.find('SITE_ID').text if registration.find('SITE_ID') is not None else 'N/A'
                
                # Perform the third API call for site details
                site_details = get_site_details(site_id)
                
                registration_details.append([freq, device_type_text, emission_desig, site_id] + site_details)
        else:
            print(f"Failed to retrieve registration details for {licence_no}: HTTP Status Code", registration_response.status_code)
    except requests.exceptions.RequestException as e:
        print(f"Request failed for {licence_no}:", e)
    
    return registration_details

# Main code to perform the first API call
api_url = "https://api.acma.gov.au/SpectrumLicensingAPIOuterService/OuterService.svc/LicenceSearchXML?searchText=VK1R&searchField=callsign&searchOption=begins%20with"

try:
    response = requests.get(api_url, timeout=10)
    if response.status_code == 200:
        root = ET.fromstring(response.content)
        csv_file = "VK1 Repeaters.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            headers = ['Licence Number', 'Client Number', 'Callsign', 'Licence Status', 'Expiry date', 'Licence Category', 'Licence Details', 'Frequency', 'Device Type', 'Emission Designator', 'Site ID', 'Site Name', 'City', 'Postcode', 'State', 'Latitude', 'Longitude', 'Site Details URL']
            writer.writerow(headers)

            for element in root.findall('.//Licence'):
                licence_category = element.find('LICENCE_CATEGORY').text
                if licence_category == "Amateur - Amateur Repeater":
                    licence_data = [element.find(tag).text if element.find(tag) is not None else 'N/A' for tag in 
                            ['LICENCE_NO', 'CLIENT_NO', 'CALLSIGN', 'STATUS_TEXT', 'DATE_EXPIRY', 'LICENCE_CATEGORY', 'DETAILS_URL']]
                    
                    # Perform the second API call for each licence number
                    registration_details_list = get_registration_details(licence_data[0])

                    # Write a row for each registration
                    for registration_details in registration_details_list:
                        writer.writerow(licence_data + registration_details)
                    
                    # Introduce a delay to respect rate limits
                    time.sleep(1) # 1 second delay; adjust as necessary based on the API's rate limit
    else:
        print("Failed to retrieve data:", response.status_code)
except requests.exceptions.RequestException as e:
    print("Request failed:", e)
