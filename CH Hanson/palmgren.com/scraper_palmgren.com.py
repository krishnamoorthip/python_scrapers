import scrapy
from scrapy.crawler import CrawlerProcess
import os, sys, re
import datetime
import time
from bs4 import BeautifulSoup
import csv

input_csv_fl = './inputs.csv'
output_csv_fl = './data_captured_superiortool.csv'

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en-GB,en;q=0.9,en-US;q=0.8,hi;q=0.7,ta;q=0.6,ko;q=0.5',
    'cache-control': 'no-cache',
    'cookie': 'CV3=pgp0l9scv31endt2cj4stl8tr2; _ga=GA1.2.1841175932.1642793442; _gid=GA1.2.1007643762.1643635771',
    'pragma': 'no-cache',
    'referer': 'https://www.palmgren.com/',
    'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="97", "Chromium";v="97"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36'
    }

def remove_intellectualsymbols(in_value):
    try:
        unwanted_symbols = "™|&trade;|&#8482;|&#x2122;|®|&reg;|&#174;|©|&copy;|&#169;|&#00A9;|℗|&#8471;|&#2117;|℠|&#8480;|&#2120;"
        uws = unwanted_symbols.split("|")
        for c_s in uws:
            in_value = in_value.replace(c_s, '')
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        log_fl.write("\nWarning Handler on: remove_intellectualsymbols()" + str(e) + "\nLine info :"+ str(exc_tb.tb_lineno))
        print("Warning Handler on: remove_intellectualsymbols()" + str(e) + "\nLine info :"+ str(exc_tb.tb_lineno))
    return in_value

def cleanhtml(raw_html,removestr,replace):
    try:
        cleanr = re.compile(removestr)
        cleantext = re.sub(cleanr, replace, raw_html)
        return cleantext
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        log_fl.write("\nWarning Handler on: cleanhtml()" + str(e) + "\nLine info :"+ str(exc_tb.tb_lineno))
        print("Warning Handler on: cleanhtml()" + str(e) + "\nLine info :"+ str(exc_tb.tb_lineno))

def trim(in_value):
    trim_val = in_value
    try:
        trim_val = trim_val.replace('\t', ' ')
        trim_val = remove_intellectualsymbols(trim_val)
        trim_val = trim_val.replace('&#8203;', '')
        trim_val = trim_val.replace('&nbsp;', ' ')
        trim_val = cleanhtml(trim_val,"\\r",' ')
        trim_val = trim_val.replace('&lt;', '<')
        trim_val = trim_val.replace('&gt;', '>')      
        trim_val = trim_val.replace('<style[\w\W]*?>[\w\W]*?</style>','')
        trim_val = trim_val.replace('<script[\w\W]*?>[\w\W]*?</script>','')
        trim_val = trim_val.replace('</p>','\n')
        trim_val = trim_val.replace('</li>','\n')
        trim_val = trim_val.replace('\"', '"')
        trim_val = trim_val.replace('&amp;', '&')
        trim_val = trim_val.replace('null', '')
        trim_val = cleanhtml(trim_val,'<[\w\W]*?>','')
        trim_val = trim_val.replace("\\u002F", "/")
        trim_val = "\n\n".join([ll.rstrip() for ll in trim_val.splitlines() if ll.strip()])
        trim_val = "\t\t".join([ll.rstrip() for ll in trim_val.split(sep='\t') if ll.strip()])
        trim_val = trim_val.replace("\n", '<br>')
        trim_val = re.sub(" +", ' ', trim_val)
        trim_val = str(trim_val.strip())
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        log_fl.write("\nWarning Handler on: trim()" + str(e) + "\nLine info :"+ str(exc_tb.tb_lineno))
        print("Warning Handler on: trim()" + str(e) + "\nLine info :"+ str(exc_tb.tb_lineno))
    return trim_val;

class DownloadPages(scrapy.Spider):
    name = 'chhanson'
    allowed_domains = ['app.salsify.com']
    
    output_csv_fl = output_csv_fl.replace('.csv', '_' + datetime.datetime.today().strftime('%Y-%m-%d %H_%M_%S') + '.csv')
    custom_settings = {'FEED_URI': output_csv_fl,
        'FEED_FORMAT': 'csv',
        'FEED_EXPORT_ENCODING': 'utf-8',
        }
    #handle_httpstatus_list = [301,503,302]#handle_httpstatus_list = [301,503,302,405]#
    handle_httpstatus_all  = True
    download_delay = 0.25
    DOWNLOADER_MIDDLEWARES = {
        'scrapy.contrib.downloadermiddleware.useragent.UserAgentMiddleware': None,
        'random_useragent.RandomUserAgentMiddleware': 405}
    ROBOTSTXT_OBEY = False
    global prod_url
    
    prod_url = 'https://www.palmgren.com/product/'
        
    def start_requests(self):
        with open(input_csv_fl, mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                ID = str(row['ID'])
                i_catalog_number = str(row['catalog_number'])
                search_url = 'https://www.palmgren.com/category/s?keyword='
                search_url = search_url + i_catalog_number
                if i_catalog_number != '':
                    yield scrapy.Request(url=search_url, callback=self.parse_products_url, dont_filter=True, headers=headers,
                         meta={'ID': ID,
                               'catalog_number': i_catalog_number})

    def parse_products_url(self, response):
        print('Inside parse_products_url()')
        ID = str(response.meta['ID'])
        i_catalog_number = str(response.meta['catalog_number'])
        hpg_src = response.text
        recs_cnt = 0
        soup = BeautifulSoup(hpg_src , 'html.parser')        
        SearchResults = soup.find("h1", attrs={"class": "page-title"})
        if SearchResults != None:
            SearchResults = SearchResults.find("p")            
            listings = soup.find("div", attrs={"class": "products"})
            if listings != None:
                all_poducts = listings.find_all("div", attrs={"class": "item-info"})
                total_listings = len(all_poducts)
                
                if total_listings > 0:                
                    for c_listing in listings:
                        try:
                            p_url = ''
                            part_num = ''
                            matched = 'No'   
                            href_html = c_listing.find("a")
                            p_url = href_html.get('href')
                            print('p_url: ' + p_url)
                            if '/product/' in p_url:
                                recs_cnt += 1
                                p_url = 'https://www.palmgren.com' + p_url
                                print('p_url: ' + p_url)
                                p_title = c_listing.find("div", attrs={"class": "product-meta"})
                                part_num = trim(p_title.text)
                                part_num = part_num.replace('SKU: ', '')
                                print('i_catalog_number: ' + i_catalog_number)
                                print('part_num: ' + part_num)
                                if i_catalog_number.upper() == part_num.upper():
                                    matched = 'Yes'
                                    print(matched)
                                    yield scrapy.Request(url=p_url,
                                        callback=self.parse_product,
                                        dont_filter=True,
                                        headers=headers,
                                        meta={'ID': ID,
                                            'catalog_number': i_catalog_number})
                        except:
                            pass

    def parse_product(self, response):
        print('Inside parse_product()')
        ID = str(response.meta['ID'])
        i_catalog_number = str(response.meta['catalog_number'])
        ppg_src = response.text
        
        image_url = ''
        additional_description = ''
        attributes = []
                    
        soup = BeautifulSoup(ppg_src, 'html.parser')
        
        img_sec = soup.find("div", attrs={"class": "product-thumbnails"})
        if img_sec != None:
            img_ele = soup.find("div", attrs={"class": "item-image"})
            if img_ele != None:
                image_url = img_ele.get('href')
                # comingsoon_full_2x.png it's not needed
                if image_url == 'https://cdn.commercev3.net/cdn.palmgren.com/images/template/comingsoon_full_2x.png':
                    image_url = ''
        
        adddes_sec = soup.find("div", attrs={"id": "tab-description"})
        additional_description = str(adddes_sec)
        
        properties_sec = soup.find_all("div", attrs={"id": "tab-specifications"})
        if len(properties_sec) > 0 :
            adddes_sec = properties_sec[0]
            adddes_eles = adddes_sec.find_all("tr")
            for c_row in adddes_eles[1:len(adddes_eles)]:
                l_td = None
                c_th = ''
                c_td = ''
                l_td = c_row.find("th")
                if l_td != None:
                    c_th = trim(l_td.text)
                    if c_th != '':
                        r_td = None
                        r_td = c_row.find("td")
                        if r_td != None:
                            c_td = trim(r_td.text)
                if c_th != '' and c_td != '':
                    c_r_val = c_th + ':' + c_td 
                    attributes.append(c_r_val)                                    
                
        yield {'ID': ID,
               'catalog_numer': i_catalog_number,
               'image_url': image_url,
               'attributes': "|".join(attributes),
               'additional_description': additional_description
               }
        	
if __name__ == "__main__":
    process = CrawlerProcess()
    process.crawl(DownloadPages)
    process.start()