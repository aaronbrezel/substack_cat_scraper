# Substack Newsletter category scraper
Substack homepage category scraper

[Substack](https://substack.com/) lists newsletters by category on its homepage. 

`subscrape.py` will scrape the name and associated information from each listed newsletter.

The results are saved in a `YYYY-MM-DD_HHMM_output.csv` file. 

Example:

`2021-05-18_1607_output.csv`
```
category,pub_name,pub_link,author,launch_date,num_subs,sub_rate,top_paid
Culture,Proof,https://sethabramson.substack.com/?utm_source=discover,Seth Abramson,4 months ago,Thousands of subscribers,$5/month,True
Culture,The Audacity.,https://audacity.substack.com/?utm_source=discover,Roxane Gay,5 months ago,Thousands of subscribers,$6/month,True
Culture,It Bears Mentioning,https://johnmcwhorter.substack.com/?utm_source=discover,John McWhorter,4 months ago,Thousands of subscribers,$5/month,True
...
```
 
