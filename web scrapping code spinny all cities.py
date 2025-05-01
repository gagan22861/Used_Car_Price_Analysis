import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

# List of cities from the image
CITIES = [
    "delhi-ncr", "bangalore", "hyderabad", "mumbai", "pune", "delhi",
    "gurgaon", "noida", "ahmedabad", "chennai", "kolkata", "lucknow", "jaipur"
]


def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def scroll_to_bottom(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def extract_car_details(soup, city):
    company = soup.find_all('div', class_='CarListingCardV2__carListingCarContainer')
    print(f"Found {len(company)} car listings in {city}")

    names = []
    years = []
    prices = []
    km_driven = []
    states = []
    transmissions = []
    fuel_types = []
    emi_per_month = []
    cities = []  # To store the city name for each car

    for i, car in enumerate(company):
        # Extract name and year
        h3_tag = car.find('h3', class_='ListingBrandModelDetail__makeModelInfo')
        if h3_tag:
            make_span = h3_tag.find('span', class_='ListingBrandModelDetail__make')
            if make_span:
                full_text = make_span.text.strip()
                parts = full_text.split()
                if len(parts) > 1:
                    year = parts[0]
                    company_name = ' '.join(parts[1:])
                    names.append(company_name)
                    years.append(year)
                else:
                    names.append("N/A")
                    years.append("N/A")
            else:
                names.append("N/A")
                years.append("N/A")
        else:
            names.append("N/A")
            years.append("N/A")

        # Multiple attempts to extract price
        price = "N/A"
        ul_tag = car.find('ul', class_='ListingPricingDetail')
        if ul_tag:
            price_span = ul_tag.find('span', class_='ListingPricingDetail__priceWithRupeeSymbol')
            if price_span:
                price = price_span.text.strip()

        if price == "N/A":
            alt_price = car.find('span', class_='price')
            if alt_price:
                price = alt_price.text.strip()

        if price == "N/A":
            all_spans = car.find_all('span')
            for span in all_spans:
                text = span.text.strip()
                if '₹' in text or 'lakh' in text.lower() or 'crore' in text.lower():
                    price = text
                    break

        prices.append(price)
        print(f"Car {i + 1} price in {city}: {price}")

        # Extract EMI per month
        emi_span = car.find('li', class_='ListingPricingDetail__emi')
        emi_per_month.append(emi_span.text.strip()[5:-3] if emi_span else "N/A")

        # Extract other details
        detail_ul = car.find('ul', class_='CarListingCardDetail__more')
        if detail_ul:
            details = detail_ul.find_all('li')
            fuel_type = "N/A"
            transmission = "N/A"
            state = "N/A"
            km = "N/A"
            for detail in details:
                text = detail.text.strip()
                text_lower = text.lower()
                if any(fuel in text_lower for fuel in ['petrol', 'diesel', "electric"]):
                    fuel_type = text
                elif any(trans in text_lower for trans in ['automatic', 'manual']):
                    transmission = text
                # Modified state detection - no regex, just look for 2 uppercase letters
                elif len(text) >= 2 and text[:2].isupper() and text[:2].isalpha():
                    state = text[:2]
                elif 'km' in text_lower:
                    km = text
            fuel_types.append(fuel_type)
            transmissions.append(transmission)
            states.append(state)
            km_driven.append(km)
        else:
            fuel_types.append("N/A")
            transmissions.append("N/A")
            states.append("N/A")
            km_driven.append("N/A")

        # Add the city name for this car
        cities.append(city)

    print(f"Extracted {len(names)} cars from {city}")
    if names:
        print("Sample data:", names[0], years[0], prices[0])

    return names, years, prices, km_driven, states, transmissions, fuel_types, emi_per_month, cities


def save_to_csv(all_data, filename='all_car_data.csv'):
    df = pd.DataFrame(all_data)
    print("Final DataFrame shape:", df.shape)
    if not df.empty:
        df.to_csv(filename, index=False)
        print(f"All data saved to {filename} with {len(df)} records")
    else:
        print("No data to save - DataFrame is empty")


def main():
    driver = setup_driver()

    # Lists to store all data
    all_names = []
    all_years = []
    all_prices = []
    all_km_driven = []
    all_states = []
    all_transmissions = []
    all_fuel_types = []
    all_emi_per_month = []
    all_cities = []

    for city in CITIES:
        print(f"\nScraping data for {city.upper()}...")
        url = f'https://www.spinny.com/used-cars-in-{city}/s/'

        try:
            driver.get(url)
            scroll_to_bottom(driver)
            time.sleep(5)

            soup = BeautifulSoup(driver.page_source, 'lxml')

            names, years, prices, km_driven, states, transmissions, fuel_types, emi_per_month, cities = extract_car_details(
                soup, city)

            # Append the data for this city to the overall lists
            all_names.extend(names)
            all_years.extend(years)
            all_prices.extend(prices)
            all_km_driven.extend(km_driven)
            all_states.extend(states)
            all_transmissions.extend(transmissions)
            all_fuel_types.extend(fuel_types)
            all_emi_per_month.extend(emi_per_month)
            all_cities.extend(cities)

        except Exception as e:
            print(f"An error occurred while scraping {city}: {str(e)}")

    driver.quit()

    # Combine all data into a single dictionary
    all_data = {
        'City': all_cities,
        'Name': all_names,
        'Year': all_years,
        'Price': all_prices,
        'Kilometers Driven': all_km_driven,
        'State': all_states,
        'Transmission': all_transmissions,
        'Fuel Type': all_fuel_types,
        'EMI per Month': all_emi_per_month
    }

    # Save all data to a single CSV file
    save_to_csv(all_data, 'Qall_car_data.csv')


if __name__ == "__main__":
    main()