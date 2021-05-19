from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time
import re
import pandas as pd

#C apture all the publications under each of the categories.
# Want category / name of publication / author / launched_date (x months ago or whatever) / # subscribers if available / subscription rate if available
# dump it into a csv



cat_div_container_xpath = "/html/body/div[1]/div/div[3]/div/div[2]/div[2]/div[2]"

show_more_categories_button_class = "show-more"

ranking_toggle_div_class = "ranking-toggle"

view_more_button_xpath = "/html/body/div[1]/div/div[3]/div/div[2]/div[1]/div[3]/button"

publication_card_css_selector = 'a.publication'

def pub_to_dict(browser, pub_element, category, ranking_toggle):
    
    # WebDriverWait(browser, 0.3).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.publication-title")))


    pub_name = pub_element.find_element_by_css_selector("div.publication-title").text
    # print(pub_name)
  
    pub_link = pub_element.get_attribute('href')

    # print(pub_name)

    
    #Parse and clean publication author and date
    pub_info = pub_element.find_element_by_css_selector("div.publication-author").text
    

    if ranking_toggle == "All":
        top_paid = False
        if len(pub_info.split("·")) == 2: 
            pub_author = pub_info.split("·")[0]
            pub_author = pub_author.replace("by", "")
            pub_author = pub_author.strip()

            pub_date = pub_info.split("·")[1]
            pub_date = pub_date.replace("Launched", "")
            pub_date = pub_date.strip()

        elif len(pub_info.split("·")) == 1:
            pub_author = ""
            pub_date = pub_info.replace("Launched", "")
            pub_date = pub_date.strip()

        num_subs = ""
        sub_rate = ""

    elif ranking_toggle == "Top paid":
        top_paid = True
        if len(pub_info.split("·")) == 3:
            pub_author = pub_info.split("·")[0]
            pub_author = pub_author.replace("by", "")
            pub_author = pub_author.strip()

            num_subs = pub_info.split("·")[1]
            num_subs = num_subs.strip()

            sub_rate = pub_info.split("·")[2]
            sub_rate = sub_rate.strip()

        elif len(pub_info.split("·")) == 2:
            
            pub_author_or_num_subs = pub_info.split("·")[0]

            if pub_author_or_num_subs.startswith("by"):
                pub_author = pub_author_or_num_subs.replace("by", "")
                pub_author = pub_author.strip()

                num_subs = ""
            else: 
                pub_author = ""
            
                num_subs = pub_author_or_num_subs.strip()
           

            sub_rate = pub_info.split("·")[1]
            sub_rate = sub_rate.strip()
        
        elif len(pub_info.split("·")) == 1:
            pub_author = ""

            num_subs = ""

            sub_rate = pub_info.split("·")[0]
            sub_rate = sub_rate.strip()


        pub_date = ""



    pub_dict = {
        'category': category, 
        'top_paid': top_paid,
        'pub_name':  pub_name,
        'pub_link': pub_link, 
        'author': pub_author, 
        'launch_date': pub_date, 
        'num_subs': num_subs, 
        'sub_rate': sub_rate
    }

    return pub_dict

def get_publications(browser, container, category, ranking_toggle):

    #First, we need to smash the view-more button until we can't anymore to get the full list of publications
    view_more = True
    while view_more:
        try:
            #Need to add a wait here untill the view more button loads
            WebDriverWait(browser, 1).until(EC.visibility_of_element_located((By.XPATH, view_more_button_xpath)))
            view_more_button = container.find_element_by_xpath(view_more_button_xpath)
            view_more_button.click()
        except:
            view_more = False
    
    



    pulling_pubs = True
    pulling_pubs_try_count = 0
    while pulling_pubs:
        try:
            pulling_pubs_try_count = pulling_pubs_try_count + 1
            #Now that we have all the publications available grab them and turn them into a list of dicts
            pub_elements = container.find_elements_by_css_selector(publication_card_css_selector)

            pub_list = []
    
            for pub_element in pub_elements:
                pub_dict = pub_to_dict(browser, pub_element, category, ranking_toggle)
                pub_list.append(pub_dict)  
            pulling_pubs = False
            print("SUCCESS")
       
        except Exception as e:
            print(e)
            print("trying again")

        if pulling_pubs_try_count > 5:
            print("Tried five times. Giving up")
            pub_list = []
            break
    if not pub_list:
        raise Exception("Error pulling pub list")

    return pub_list

def match_pub_row(comp_substack_df, pub_dict):
    
    matching_index = comp_substack_df.loc[comp_substack_df['pub_link'] == pub_dict['pub_link']].index.values

    return matching_index

class SubmitChanged(object):
    def __init__(self, element, xpath):
        
        self.element = element
        self.xpath = xpath
        self.text = element.text


    def __call__(self, driver):
        # here we check if this is new instance of element
        new_element = driver.find_element_by_xpath(self.xpath)
        return new_element.text != self.text

        

def traverse_substack(browser):

    
    substack_df = pd.DataFrame(columns = ['category', 'top_paid', 'pub_name', 'pub_link', 'author', 'launch_date', 'num_subs', 'sub_rate'])


    #Step 1: set content container
    container = browser.find_element_by_xpath("/html/body/div[1]/div/div[3]/div")

    # Step 2: expand Categories section
    show_more_cat_button = container.find_element_by_class_name(show_more_categories_button_class)
    show_more_cat_button.click()

    # Step 3: Get list of category buttons to click
    cat_div = container.find_element_by_xpath(cat_div_container_xpath)
    cat_buttons = cat_div.find_elements_by_tag_name("button")
    cat_buttons = cat_buttons[1:] #Removing "Featured button as it would be repetitive"

    # Step 4: Set ranking toggle to "Top paid" for first scrape pass
    ranking_toggle = None
    cat_buttons[0].click() 

    ranking_toggle_wait = WebDriverWait(browser, 3)
    ranking_toggle_wait.until(EC.presence_of_element_located((By.CLASS_NAME,ranking_toggle_div_class)))

    ranking_toggle_div = container.find_element_by_class_name(ranking_toggle_div_class)
    ranking_links = ranking_toggle_div.find_elements_by_tag_name("a")
    for ranking_link in ranking_links:
        if ranking_link.text == "Top paid":
            ranking_link.click()
            ranking_toggle = "Top paid"

    # Step 5: Iterate through each category and scrape publications
    # (ignore Featured as the info will be repetitive)
    for cat_button in cat_buttons:

        test = SubmitChanged(browser.find_element_by_xpath("/html/body/div[1]/div/div[3]/div/div[2]/div[1]/div[2]/a[1]/div[2]/div[2]/div[1]"), "/html/body/div[1]/div/div[3]/div/div[2]/div[1]/div[2]/a[1]/div[2]/div[2]/div[1]")    

        # Nav to category page
        cat_button.click()
        try:  
            wait = WebDriverWait(browser, 4)
            wait.until(test)
        except:
            pass
        

        #Scrape publications into list of dicts
        list_of_publications = get_publications(browser, container, cat_button.text, ranking_toggle)
        
        #Append list of dicts to dataframe
        substack_df = substack_df.append(list_of_publications, ignore_index=True)
    
      

        # break

    # Step 6: Set ranking toggle to "All" for second scrape pass
    ranking_toggle_div = container.find_element_by_class_name(ranking_toggle_div_class)
    ranking_links = ranking_toggle_div.find_elements_by_tag_name("a")
    for ranking_link in ranking_links:
        if ranking_link.text == "All":
            ranking_link.click()
            ranking_toggle = "All"
    cat_buttons[0].click()


    #Step 7: Create a deep copy of substack_df to compare results of second scrape pass more quickly
    # We will still append newly scraped pubs to the original substack_df
    comp_substack_df = substack_df.copy(deep=True)


    # Step 8: Iterate through each category and scrape publications
    # But instead of immediately appending them to substack df, we need to check whether they are already in the deep-copied dataframe
    for cat_button in cat_buttons:
        
        
    
        test = SubmitChanged(browser.find_element_by_xpath("/html/body/div[1]/div/div[3]/div/div[2]/div[1]/div[2]/a[1]/div/div[2]/div[1]"), "/html/body/div[1]/div/div[3]/div/div[2]/div[1]/div[2]/a[1]/div/div[2]/div[1]")    
        
        # Nav to category page
        cat_button.click() 
        try:
            wait = WebDriverWait(browser, 3)
            wait.until(test)
        except:
            pass
        

        #Scrape publications into list of dicts
        list_of_publications = get_publications(browser, container, cat_button.text, ranking_toggle)

        #Iterate through each new publication added. If pub is already in substack_df, add just launch date. If not, append whole thing
      
        for pub_dict in list_of_publications:
           
            matching_index =  match_pub_row(comp_substack_df, pub_dict)
           
            if matching_index.size > 0:
                # print("Match")
                substack_df.loc[matching_index,['launch_date']] = pub_dict['launch_date']
          
                
            else: 
                substack_df = substack_df.append(pub_dict, ignore_index=True)
                # print("No Match")
                    
    return substack_df




if __name__ == '__main__':

    browser = webdriver.Firefox()
    browser.get("https://substack.com/home")
    substack_df = traverse_substack(browser)

    file_prefix = re.sub(r'\..*', '', str(datetime.now()).replace(' ', '_')).replace(':', '')[:-2]
    substack_df.to_csv(f"{file_prefix}_output.csv", index=False)
    browser.quit()