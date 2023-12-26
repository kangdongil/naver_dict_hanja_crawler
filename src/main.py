import csv
from logger import logger
from selenium_driver import SeleniumDriver
from selenium.webdriver.common.by import By
from hanja_tool import hanja_to_url, standardize_hanja


def get_hanja_data(hanja, browser):
    """
    Retrieve Hanja information from the Naver Hanja Dictionary website.

    :param hanja: The Hanja character to search for.
    :type hanja: str
    :param browser: An instance of the SeleniumDriver class for web automation.
    :type browser: SeleniumDriver
    :returns: A tuple containing Hanja character, its unique ID, and detailed information.
    :rtype: tuple
    """

    # Step 1: Fetch Hanja data from the Naver Dictionary website
    encoded_hanja = hanja_to_url(hanja)
    url = f"https://hanja.dict.naver.com/search?query={encoded_hanja}"
    browser.get_await(url=url, locator=(By.ID, "searchPage_letter"))

    hanja_obj = browser.find_elements(By.CSS_SELECTOR, ".row")[0].find_element(
        By.CSS_SELECTOR, ".hanja_word .hanja_link"
    )

    # Step 2: Extract the Hanja ID
    if hanja_obj.text == standardize_hanja(hanja):
        hanja_id = hanja_obj.get_attribute("href").split("/")[-1]
    else:
        return (hanja, None, None)

    # Step 3: Access the Detail Webpage with Hanja ID
    detailed_url = f"https://hanja.dict.naver.com/#/entry/ccko/{hanja_id}"
    browser.get_await(url=detailed_url, locator=(By.CLASS_NAME, "component_entry"))

    # Step 4: Save WebElements for repetitive calls
    hanja_entry = browser.find_element(By.CSS_SELECTOR, ".component_entry")
    hanja_infos = hanja_entry.find_elements(By.CSS_SELECTOR, ".entry_infos .info_item")

    # Step 5: Extract Hanja Information from web crawling
    hanja_meaning = hanja_entry.find_element(By.CSS_SELECTOR, ".entry_title .mean").text
    hanja_radical = hanja_infos[0].find_element(By.TAG_NAME, "button").text
    hanja_stroke_count = int(
        hanja_entry.find_element(
            By.CSS_SELECTOR, ".entry_infos .stroke span.word"
        ).text[:-1]
    )
    if hanja_infos[1].find_element(By.CSS_SELECTOR, ".info_item .cate").text == "모양자":
        formation_letters = (
            hanja_infos[1].find_element(By.CSS_SELECTOR, ".desc").text.split(" + ")
        )
        formation_letter = tuple(seg[0] for seg in formation_letters)
    else:
        formation_letter = None
    unicode = hanja_infos[2].find_element(By.CLASS_NAME, "desc").text
    usage = tuple(
        usage.text
        for usage in hanja_entry.find_elements(
            By.CSS_SELECTOR, ".entry_condition .unit_tooltip"
        )
    )
    # Step 6: Create a dictionary with Hanja information
    hanja_info = {
        "Meaning": hanja_meaning,
        "Radical": hanja_radical,
        "Stroke Count": hanja_stroke_count,
        "Formation Letter": formation_letter,
        "Unicode": unicode,
        "Usage": usage,
    }

    # Step 7: Create a tuple with Hanja character, its unique ID, and detailed information
    data = (hanja, hanja_id, hanja_info)

    return data


def export_to_csv(fieldnames, data):
    """
    Export data to a CSV file.

    :param file_name: The name of the CSV file to export.
    :type file_name: str
    :param fieldnames: A list of field names for the CSV header.
    :type fieldnames: list
    :param data: A list of dictionaries containing data to be exported to the CSV file.
    :type data: list
    """
    with open("data/hanja_result.csv", "w", newline="", encoding="utf-8") as csvfile:
        csvwriter = csv.DictWriter(csvfile, fieldnames=fieldnames)
        csvwriter.writeheader()

        for row in data:
            csvwriter.writerow(row)


def main():
    """
    Main function for performing web scraping of Hanja data and exporting it to a CSV file.

    This function initializes a SeleniumDriver instance, fetches Hanja data for a list of Hanja characters,
    and exports the data to a CSV file named 'hanja_result.csv'.

    :return: None
    """
    # Create a SeleniumDriver instance with common options
    browser = SeleniumDriver()

    # Create an empty list to store the results
    results = []

    # List of Hanja characters to search for
    hanja_list = [
        "校",
        "六",
        "萬",
        "母",
        "木",
        "門",
        "民",
    ]

    # Iterate through the list of Hanja characters and fetch their data
    for idx, hanja in enumerate(hanja_list, 1):
        result = get_hanja_data(hanja, browser)
        results.append(result)
        if result[1] != None:
            logger.info(f"[{idx} / {len(hanja_list)}] {hanja}'s data has been fetched.")
        else:
            logger.error(f"[{idx} / {len(hanja_list)}] Fetch Failed: {hanja}'")

    # Close the browser session to relase resources
    browser.quit()
    logger.info("WebCrawling Finished.")

    # Define the CSV header
    fieldnames = [
        "hanja",
        "meaning",
        "radical",
        "stroke_count",
        "formation_letter",
        "unicode",
        "usage",
        "naver_hanja_id",
    ]

    # Align data with fieldnames
    csv_data = []
    for result in results:
        if result[1] is not None:  # Temporary for fixing bug
            csv_data.append(
                {
                    "hanja": result[0],
                    "meaning": result[2]["Meaning"],
                    "radical": result[2]["Radical"],
                    "stroke_count": result[2]["Stroke Count"],
                    "formation_letter": ", ".join(result[2]["Formation Letter"]),
                    "unicode": result[2]["Unicode"],
                    "usage": ", ".join(result[2]["Usage"]),
                    "naver_hanja_id": result[1],
                }
            )

    # Epxort the results to CSV
    export_to_csv(fieldnames, csv_data)
    logger.info("CSV Export Finished")


if __name__ == "__main__":
    main()
