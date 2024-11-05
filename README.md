The following link links out to the "Comprehensive Methodology Report":
https://data.cms.gov/provider-data/topics/hospitals/overall-hospital-quality-star-rating

Based on my research, here are the CSV files that CMS draws from to compute the star ratings. (i.e. They use these source files to build the SAS7BDAT file.) 

healthcare_associated_infections-hospital
cms_psi_6_decimal_file
complications_and_deaths-hospital
hcahps-hospital
hospital_general_information
hvbp_clinical_outcomes
outpatient_imaging_efficiency-hospital
timely_and_effective_care-hospital
unplanned_hospital_visits-hospital
va_te

Note that from quarter to quarter, the column headers may change. You'll want to build a generic staging table that can load all the data and tag with the appropriate quarter. That way, you can run a few queries and generate your own SAS7BDAT file for any combination of quarters. 

You won't need SAS, but looking at the SAS code (possibly with the help of ChatGPT to understand what's going on) could be helpful in seeing how CMS transforms the raw data into the Star Rating. The SAS Input File (*.sas7bdat) can be read using the SAS7BDAT package in R (or similar Python package) and converted to CSV.
https://qualitynet.cms.gov/inpatient/public-reporting/overall-ratings/sas

As for how to deal with the large files, or design a staging database that works for your needs, these will be good questions for Dr. Chung. 

I am good with our Monday check-ins for progress report. If you send questions M-F, I will try to answer them within a couple days, if not sooner. 

The target audience is Healthcare Quality leadership, in terms of business questions when we get to that point. 

Dr. Koehl
