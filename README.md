# Installation

Instructions for installing the system. Detailed instructions for setting up the chatbot
functionality are located in the project report.

## Prerequisites
- Windows 10 or Mac - Other operating systems are untested
- Google Chrome or Safari Browser - Some functionality may not work correctly with Firefox
- Python 3 - https://www.python.org/downloads/ 
- Pip3 - https://pip.pypa.io/en/stable/installing/
- Git - https://git-scm.com/downloads
- ngrok - https://ngrok.com/

## Downloading project and packages
1. Clone the project repository into the desired directory with the command:
 `git clone git@github.com:unsw-cse-comp3900-9900-21T1/capstone-project-3900-w18a-let-s-chat.git`
2. Next you must install the project’s required packages. Navigate to the project’s root directory and run the command:
 `pip3 install -r requirements.txt`
 This should install the python packages required by the system, such as Django, Pillow and Pinax messages.

## Setting up the chatbot functionality
Please refer to the project report for an easier to follow version of these instructions with images.

Our team has set "ali.darejeh@unsw.edu.au" as one of the developers for the DialogFlow agent (Petiverse). Please contact him or wellsontan@hotmail.co.uk to grant permission for the further action.
The chatbot with all the working functionalities will require a public url generator, the corresponding DialogFlow agent (Petiverse) and Kommunicate web script. Currently, the github code has included a working chatbot which has a valid Kommunicate appID that can last for 30 days (expires in 21 May 2021). If the chatbot is missing from the web pages that could mean the appID is no longer working, please refer to “Kommunicate free trial expired do this” section. Or else just follow “Get a public url to enable DialogFlow webhook functionality” to start the chatbot. 


### Getting a public url to enable DialogFlow webhook functionality
**Download:**
Download ngrok and generate a temporary public url (2 hours long): 
https://ngrok.com/
After downloading the zipped file, ‘Extract all’  and run the ngrok.exe file and the ngrok command prompt will pop up. 

**Replacement:**
Enter `ngrok http 8000` in the command prompt to trigger the public url generation.
After the url has been generated copy the code in the generated url:
Eg. if the generated url reads http://5b5fe19e9f6.ngrok.io, copy 5b5fe19e9f6.

Next, go to the DialogFlow fulfilment section and replace the highlighted part with the copied text and save it. Then, the ‘Save’ button will read ‘Done’.

Note: Please always include ‘/webhook/’ in the URL section. Do not remove that. Additonally, the webhook requires a https url.

After changing the DialogFlow fulfilment part, return to ecommerce/ecommerce/settings.py and replace the expired ngrok url in ALLOWED_HOSTS with the new ngrok generated url.

Remember each public url generated from ngrok will only last for 2 hours. Therefore, to extend the usage period please repeat the ‘Replacement’ part. The webhook fulfilment is used on product_searching, product_enquiry and place_bid features. The rest of the features will not require the Dialogflow webhook to function.

### If the Kommunicate free trial has expired, do this:

Accessing the web script:
1. Sign up to Kommunicate and retrieve the web script at https://dashboard.kommunicate.io/signup?product=kommunicate
2. Copy the script provided by Kommunicate and paste it into store/templates/store/main.html, removing the previous, similar looking Kommunicate script.

Integrating Kommunicate with Dialogflow:
1. Return to the Kommunicate website and under the 'integrate your bot with Kommunicate' section choose 'Dialogflow ES'.
2. Drag the file 'ecommerce/store/petiverse-sqtd-211b8b43d7aa.json' into the private key section. Leave the remaining fields
and click 'Save and proceed'.
3. After that, you will be prompted to customise the appearance of the chatbot. Once again, click 'Save and proceed'.
4. On the final page, choose to disable 'Automatic bot to human handoff' and click 'Finish bot setup' to complete the bot integration.

### Running the server

Once all setup steps have been completed, the site server should be ready to run. To run the server, ensure you are in the project root directory and run the command:
`python3 ecommerce/manage.py runserver`
This will start the project development server, and the website can now be accessed locally on your browser through the localhost address 127.0.0.1:8000. The website will use our existing test database, stored in the file ecommerce/db.sqlite3. This database contains some test users and products, to demonstrate site functionality such as store pages, purchasing, and the recommendation system.

An existing admin account that can be used to inspect the site has the username *danny*, and the password *unsw2021*. If you wish to create your own account you can do so using the signup page on the website. This account can then be promoted to admin status using the admin site at the path /admin while logged in to an existing admin user. The admin site allows existing admins to freely view and modify the site database, and take actions such as deleting or modifying users, or even clearing all records if you wish to experiment with a fresh database.
