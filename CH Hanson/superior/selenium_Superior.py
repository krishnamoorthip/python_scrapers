#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys, time, re, signal
from selenium import webdriver
from datetime import date
import datetime
from bs4 import BeautifulSoup
import csv
import pandas as pd

input_csv_fl = 'inputs.csv'
output_csv_fl = 'output_superiortool.com.csv'

# Source site: https://www.superiortool.com/
# This site is exact similar to https://www.chhanson.com except differ APP url
# APP url: https://app.salsify.com/catalogs/ebb6f615-73e3-485c-9ee5-0fceeeafae05/products/18610

app_url = 'https://app.salsify.com/catalogs/ebb6f615-73e3-485c-9ee5-0fceeeafae05/products/IN_CATALOG_NUM'
##IN_CATALOG_NUM for replacing input catalog#

##handling webderiver connection
chromeOptions = webdriver.ChromeOptions()
chromeOptions.add_argument("--start-maximized");
#prefs = {"profile.managed_default_content_settings.images":2}
#chromeOptions.add_experimental_option("prefs",prefs)

driver = ''

def opendriver():
    try:
        driver = webdriver.Chrome('c:/chromedriver.exe', chrome_options=chromeOptions)
        driver.get('https://app.salsify.com/catalogs/ebb6f615-73e3-485c-9ee5-0fceeeafae05/products/18610')
        time.sleep(10)
        ##Clicking on Accept button for cooking
        try:
            driver.find_element_by_class_name('_accept-button_c4rx6v').click()        
            time.sleep(6)
        except:
            pass
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        log_fl.write("\n\tError Handler on 'opendriver()': " + str(e))
        log_fl.write("\n\t\tLine info :"+ str(exc_tb.tb_lineno))
        print("Error Handler on 'opendriver()': " + str(e))
        print("Line info :"+ str(exc_tb.tb_lineno))
    return driver

def closedriver():
    if driver != "":
        driver.close()
        driver.service.process.send_signal(signal.SIGTERM) # kill the specific phantomjs child proc
        driver.quit()

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

def extract_data(in_internal_id, in_catalog_num, ppg_src):
    try:
        product_id = ''
        image_url = ''
        add_des = ''
        attributes = []
        matched = ''
        
        soup = BeautifulSoup(ppg_src, 'html.parser')
        
        img_sec = soup.find("div", attrs={"class": "product-profile-image"})
        if img_sec != None:
            img_ele = soup.find("a", attrs={"class": "mfp-image"})
            if img_ele != None:
                image_url = img_ele.get('href')
        
        cur_ele = None
        cur_ele = re.search('<div class="product-property-value">([\w\W]*?)</span>', ppg_src)
        if cur_ele != None:
            product_id = trim(cur_ele.group(1))
        
        properties_sec = soup.find_all("div", attrs={"class": "product-properties"})
        if len(properties_sec) > 0 :
            adddes_sec = properties_sec[0]
            adddes_eles = adddes_sec.find_all("div", attrs={"class": "row"})
            for c_row in adddes_eles[0:len(adddes_eles)]:
                l_td = None
                c_th = ''
                c_td = ''
                l_td = c_row.find("span", attrs={"class": "product-property-name"})
                if l_td != None:
                    c_th = trim(l_td.text)
                    if c_th != '':
                        c_th = '<th>' + c_th + '</th>'
                        r_td = None
                        r_td = c_row.find("div", attrs={"class": "product-property-value"})
                        if r_td != None:
                            c_td = trim(r_td.text)
                            c_td = '<td>' + c_td + '</td>'
                if c_th != '' and c_td != '':
                    c_r_val = '<tr>' + c_th + c_td + '</tr>' 
                    if add_des == '':
                        add_des = c_r_val
                    else:
                        add_des = add_des + c_r_val    
            if add_des != '':
                add_des = '<table class="description-table">' + add_des + '</table>'   
            if len(properties_sec) > 1 :
                attrs_sec = properties_sec[1]
                attrs_eles = attrs_sec.find_all("div", attrs={"class": "row"})
                for c_row in attrs_eles[0:len(attrs_eles)]:
                    l_td = None
                    c_th = ''
                    c_td = ''
                    l_td = c_row.find("span", attrs={"class": "product-property-name"})
                    if l_td != None:
                        c_th = trim(l_td.text)
                        if c_th != '':
                            r_td = None
                            r_td = c_row.find("div", attrs={"class": "product-property-value"})
                            if r_td != None:
                                c_td = trim(r_td.text)
                    if c_th != '' and c_td != '':
                        c_attr = c_th + ':' + c_td
                        attributes.append(c_attr)
        c_outs = []            
        c_outs.append(in_internal_id)                    
        c_outs.append(in_catalog_num)
                              
        if product_id.upper() == in_catalog_num.upper():
            matched = 'Yes'
            attributes = "|".join(attributes)
            c_outs.append(image_url)
            c_outs.append(attributes)
            c_outs.append(add_des)
            
        output_list.append(c_outs)
        if product_id != '':
            print('result found and scraped')
        else:
            print('no result found')
        log_fl.write(str(in_internal_id) + '\t\"' + in_catalog_num + '\"\t\"' + product_id + '\"\t\"' + matched + '\"\t\"' + image_url + '\"\t\"' + attributes + '\"\t\"' + add_des + '\"\n')
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        log_fl.write("\nWarning Handler on: extract_data()" + str(e) + "\nLine info :"+ str(exc_tb.tb_lineno))
        print("Warning Handler on: extract_data()" + str(e) + "\nLine info :"+ str(exc_tb.tb_lineno))
    
if __name__ == "__main__":
    starttime = time.strftime("%Y-%m-%d %H_%M_%S")
    print("Script started time: "+starttime)
    log_fl = open('log_fl.txt', 'w', encoding='utf-8')
    log_fl.write("\nScript started time: "+starttime)
    inputs = []
    output_list = []
    try:
        header = []
        driver = opendriver()
        with open(input_csv_fl) as csvfile:
            inputs = csv.reader(csvfile, delimiter=',')
            header = next(inputs)        
            header_cols = ",".join(header)
            header_cols = header_cols + ",image_url,attributes,add_description"
            entry = header_cols.split(',')
            output_list.append(entry)
            
            in_count = 1
            for crow in inputs:   
                try:
                    in_internal_id = str(crow[0])
                    print('\nCount: ' + str(in_count) + '\t' + in_internal_id)
                    in_catalog_num = str(crow[1])
                    log_fl.write('\nCount: ' + str(in_count))                
                    log_fl.write('\n' + in_internal_id + '\t' + in_catalog_num + '\t')
                         
                    s_url = app_url
                    s_url = s_url.replace('IN_CATALOG_NUM', in_catalog_num)
                    
                    ppg_src = ''
                    
                    driver.get(s_url)
                    time.sleep(10)    
                    ppg_src = driver.page_source
                    
                    extract_data(in_internal_id, in_catalog_num, ppg_src)
                    ppg_src = ''
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    log_fl.write("\nError Handler2: "+ str(e) + "\nLine info :"+ str(exc_tb.tb_lineno))
                    print("Error Handler2: "+ str(e) + "\nLine info :"+ str(exc_tb.tb_lineno))
                log_fl.flush()
                in_count += 1
        output_csv_fl = output_csv_fl.replace('.csv', '_' + starttime + '.csv')
        with open(output_csv_fl, 'w', newline='', encoding='utf-8') as f2:
            csv_writer = csv.writer(f2)
            csv_writer.writerows(output_list)            
                        
        f2.close()
        
        endtime = time.strftime("%Y-%m-%d %H_%M_%S")
        log_fl.write("\n\nScript ended time: "+endtime)
        print("\nScript ended time: "+endtime)
        
        log_fl.flush()
        log_fl.close()
        closedriver()
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        log_fl.write("\nError Handler1: "+ str(e) + "\nLine info :"+ str(exc_tb.tb_lineno))
        print("Error Handler1: "+ str(e) + "\nLine info :"+ str(exc_tb.tb_lineno))
        log_fl.flush()