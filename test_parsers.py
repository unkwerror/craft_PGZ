from parsers.search_parser import ZakupkiSearch
from parsers.tender_parser import ZakupkiTender

def test_search_parser():
    print("=== Тест ZakupkiSearch ===")
    with ZakupkiSearch(headless=True) as search_parser:
        search_parser.open_site()
        search_parser.set_filters()
        search_parser.search_query("проектирование екатеринбург")
        results = search_parser.parse_orders(limit=3)
        for r in results:
            print(r)
        return results

def test_tender_parser(reg_number: str):
    print(f"\n=== Тест ZakupkiTender для закупки {reg_number} ===")
    with ZakupkiTender(headless=True) as tender_parser:
        tender_parser.load_page(reg_number)
        info = tender_parser.parse_documents()
        print("Найдено документов:", len(info))
        for doc in info[:3]:
            print(doc)

if __name__ == "__main__":
    search_results = test_search_parser()
    
    if search_results:
        # Берем первую закупку из результатов поиска
        first_reg_number = search_results[0]["number"]
        test_tender_parser(first_reg_number)
