import os
import time
import openai
import telebot
import pymongo
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv() 
DB_USERNAME = os.environ['DATABASE']
DB_PASSWORD = os.environ['DB_PASSWORD']
openai.api_key = os.environ['OPEN_AI_KEY']

client = pymongo.MongoClient(f"mongodb+srv://{DB_USERNAME}:{DB_PASSWORD}@cluster0.1e3sslc.mongodb.net/?retryWrites=true&w=majority")
db=client.learning_mongodb


# Define a function to test the API
# def test_openai_api():
#     try:
#         # Make a test API call
#         response = openai.Completion.create(
#             engine='davinci',
#             prompt='Hello, world!',
#             max_tokens=5
#         )
#         return True
#     except Exception as e:
#         print(f"OpenAI API test failed: {str(e)}")
#         return False

# Call the test function
# if test_openai_api():
#     print("OpenAI API is working!")
# else:
#     print("OpenAI API is not working.")
# player_info=db.player.find({})
# print(list(player_info))


# Global Variables
scraped_data = None
all_data = None
previous_job = None
previous_db = None
branches = {
    "Eligibility":"Eligibility",
    "Automotive Engineering": "AE",
    "Bio-Technology Engineering": "BT",
    "Chemical Engineering": "CE",
    "Civil Engineering": "CE",
    "Computer Engineering": "COE",
    "Electronics and Communications Engineering": "ECE",
    "Electrical Engineering": "EE",
    "Environmental Engineering": "EN",
    "Engineering Physics": "EP",
    "Information Technology": "IT",
    "Mathematics and Computing": "MCE",
    "Mechanical Engineering": "ME",
    "Polymer Science and Chemical Technology": "PSCT",
    "Production and Industrial Engineering": "PIE",
    "Software Engineering": "SE"
}

user_ids = []

APIKEY = os.environ['API_KEY']
bot = telebot.TeleBot(APIKEY)

# Function to get user IDs from the database
user_ids_dict = list(db.user.find({}, {"_id": 0, "userid": 1}))
user_ids = list(map(lambda item: item["userid"], user_ids_dict))

print("userids",user_ids)

# Post the data to your channel
channel_id = 'CHANNEL_ID'


@bot.message_handler(commands=['update'])
def update2(message):
  global user_ids
  user_ids_dict = list(db.user.find({}, {"_id": 0, "userid": 1}))
  user_ids = list(map(lambda item: item["userid"], user_ids_dict))
  user_id=message.chat.id
  if user_id in user_ids:
    bot.send_message(user_id, all_data)
  else:
    bot.reply_to(message, 'You have not granted permission.')

def update(user_id, data):
  global user_ids, all_data, scraped_data
  user_ids_dict = list(db.user.find({}, {"_id": 0, "userid": 1}))
  user_ids = list(map(lambda item: item["userid"], user_ids_dict))
  # jobs_updates()
  if user_id in user_ids:
    bot.send_message(user_id, data)

# Handler for the command to ask for permission
@bot.message_handler(commands=['permission'])
def ask_permission(message):
  global user_ids
  user_ids_dict = list(db.user.find({}, {"_id": 0, "userid": 1}))
  user_ids = list(map(lambda item: item["userid"], user_ids_dict))
  user_id = message.chat.id
  if user_id not in user_ids:
    bot.reply_to(message,
                 'You have granted permission to receive automated messages.')
    db.user.insert_one({"userid": user_id})
  else:
    bot.reply_to(message, 'You have already granted permission.')


# Handler for the command to revoke permission
@bot.message_handler(commands=['revoke'])
def revoke_permission(message):
  global user_ids
  user_ids_dict = list(db.user.find({}, {"_id": 0, "userid": 1}))
  user_ids = list(map(lambda item: item["userid"], user_ids_dict))
  user_id = message.chat.id
  if user_id in user_ids:
    bot.reply_to(message,
                 'You have revoked permission to receive automated messages.')
    db.user.delete_many({"userid":user_id})
  else:
    bot.reply_to(message, 'You have already revoked permission.')


@bot.message_handler(commands=['start'])
def handle_start(message):
  # Prepare the list of commands
  commands = [
    '/permission - Permitting the bot to send you messages after every hoour',
    '/revoke - Revoke your permission', '/update - New Jobs/ Updates',
    '/search - Search for your Query'
    # Add more commands here
  ]

  # Format the commands as a string
  commands_text = '\n'.join(commands)

  # Send the commands to the user
  bot.send_message(message.chat.id, f'Available commands:\n{commands_text}')

@bot.message_handler(commands=['help'])
def send_commands(message):
    keyboard = InlineKeyboardMarkup(row_width=1)
    commands = [
        {'text': 'Permission', 'callback_data': 'permission'},
        {'text': 'Revoke', 'callback_data': 'revoke'},
        {'text': 'Update', 'callback_data': 'update'},
        {'text': 'Search', 'callback_data': 'search'},
        {'text': 'Start', 'callback_data': 'start'}
    ]

    for command in commands:
        button = InlineKeyboardButton(command['text'], callback_data=command['callback_data'])
        keyboard.add(button)

    bot.send_message(message.chat.id, "Select a command:", reply_markup=keyboard)

def search(query):
  response = openai.Completion.create(
  model="text-davinci-003",
  prompt=query,
  temperature=0.2,
  max_tokens=1024,
  top_p=1,
  frequency_penalty=0.0,
  presence_penalty=0.0,
)
  return response.choices[0].text.strip()

@bot.message_handler(commands=['ask'])
def handle_ask_command(message):
    bot.reply_to(message, "Please enter your query")
    bot.register_next_step_handler(message, process_query)

def process_query(message):
    query = message.text
    result = search(query)
    bot.reply_to(message, result)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    command = call.data

    if command == 'permission':
        # Handle command 1
      bot.send_message(call.message.chat.id, "Permission")
      ask_permission(call.message)

    elif command == 'revoke':
        # Handle command 2
      bot.send_message(call.message.chat.id, "Revoke")
      revoke_permission(call.message)

    elif command == 'update':
        # Handle command 3
      bot.send_message(call.message.chat.id, "Update")
      update(call.message)

    elif command == 'search':
        # Handle command 4
      bot.send_message(call.message.chat.id, "Search")
      search(call.message)

chrome_options = Options()
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=chrome_options)

# global scraped_data, previous_db, previous_job, all_data, user_ids, branches

loginurl = ('https://rm.dtu.ac.in/api/auth/login')
secure_url = ('https://www.rm.dtu.ac.in/app/dashboard')

# Login Credentials

rollNo = str(os.environ['ROLLN'])
password = str(os.environ['PASSW'])

# Navigate to the desired website
driver.get(loginurl)

RN = driver.find_element(
  By.CLASS_NAME, 'css-1t8l2tu-MuiInputBase-input-MuiOutlinedInput-input')
RN.send_keys(rollNo)

SK = driver.find_element(
  By.CLASS_NAME, 'css-nxo287-MuiInputBase-input-MuiOutlinedInput-input')
SK.send_keys(password)

# time.sleep(5)
submit_button = driver.find_element(
  By.XPATH, "//button[@type='submit']"
)  # Replace with the actual XPath or other locator of the submit button
submit_button.send_keys(Keys.ENTER)
time.sleep(5)

print("logged in successfully")

# Get the current URL
current_url = driver.current_url

# Display the current URL
print("Current URL:", current_url)

# Get the page source from Selenium
page_source = driver.page_source

soup = BeautifulSoup(page_source, 'html.parser')

# Find all div elements with a specific class name
div_elements = soup.find_all('div', class_='css-wdtwov-MuiGrid-root')

div_elements_first_three = div_elements[:2]

rev_div_elements = div_elements_first_three[::-1]
all_data = "-------RM Dashboard-------\n"
# Iterate over the div elements and perform actions
for div in rev_div_elements:
  # Perform actions on each div element
  companyname = div.find('p', class_='css-1v1tjum-MuiTypography-root').text
  companystatus = div.find_all('p', class_='css-ahj2mt-MuiTypography-root')
  # Print the name and status
  nm = "Name: " + companyname + "\n"
  pt = ""
  for p in companystatus:
    pt += p.text + "\n"
  current_db = nm + pt + "\n"
  all_data += current_db +"---------------------------------\n\n"
if previous_db == current_db:
  previous_db = current_db
else:
  previous_db = current_db
  rmmessage = "-------RM Dashboard-------\n"
  scraped_data = rmmessage + current_db + "---------------------------------\n"
  for user_id in user_ids:
    update(user_id,scraped_data)

# Jobs Panel
time.sleep(1)

jobs = driver.find_element(By.XPATH, ".//a[@href='/app/jobs']")

jobs.send_keys(Keys.ENTER)

time.sleep(1)

# Get the current URL
current_url = driver.current_url

# Display the current URL
# print("Current URL:", current_url)

page_jobs_source = driver.page_source

soup = BeautifulSoup(page_jobs_source, 'html.parser')

# Find all div elements with a specific class name
div_elements = soup.find_all('div', class_='css-wdtwov-MuiGrid-root')

div_elements_first_three = div_elements[:3]
latest_job = div_elements[0]
rev_div_elements = div_elements_first_three[::-1]
all_data += "--------Jobs Updated--------\n"
# Iterate over the div elements and perform actions
div=latest_job
# for div in rev_div_elements:
# Perform actions on each div element
companyname = div.find('div', class_='css-dsnyvo')
companystatus = div.find('div', class_='css-155ff3i')
p_job_status = companystatus.find_all(
  'p', class_="css-ahj2mt-MuiTypography-root")
nam = "Name: " + companyname.h5.text + "\n"

# Print the name and status
ptot = ""
for job_status in p_job_status:
  ptot += "" + job_status.text + "" + "\n"
current_job = nam + ptot
print("Know More")
KMore = driver.find_element(By.XPATH, '/html/body/div/div/div[3]/div/div/div/div[1]/div/div/div[2]/div/div[1]/div/div/div[2]/a[1]/button')
KMore.send_keys(Keys.ENTER)
time.sleep(5)
current_url = driver.current_url
print(current_url)

page_jobs_source = driver.page_source
soup = BeautifulSoup(page_jobs_source, 'html.parser')
# Extract form link and close date
form_link = soup.find('p',class_='MuiTypography-root MuiTypography-body1 css-ahj2mt-MuiTypography-root').text

fdes=form_link
# Extract close date from form
# close_date = soup.find_all('p', class_='MuiTypography-root MuiTypography-body1 css-1qqynwt-MuiTypography-root')
# ctime=""

# for close_date in close_date:
#     ctime+= close_date.text+"\n"

# Extract job description
anchor_element = soup.find('a')
link = anchor_element['href']
job_description = soup.find('p', class_="MuiTypography-root MuiTypography-body1 css-z2eky3-MuiTypography-root").text
jdes=job_description
print(jdes)
# Display the extracted job description

# Find the dropdown menu element (div)
wait = WebDriverWait(driver, 10)  # Set an appropriate waiting time
# Locate the element and wait until it is clickable
element = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/div/div[3]/div/div/div/div[8]/table/tbody/tr[1]/td[2]/div/div/div/div")))

# Click on the element
element.send_keys(Keys.ENTER)

# Find the ul element containing the branch names
ul_element = element.find_element(By.XPATH, "//ul[@class='MuiList-root MuiList-padding MuiMenu-list css-6hp17o-MuiList-root-MuiMenu-list']")

# Find all the li elements within the ul element
li_elements = ul_element.find_elements(By.TAG_NAME, "li")

# Iterate over the li elements and print their text
branch_Name="Eligibility: "
for li in li_elements:
    branch_name = li.text
    if branch_name and branch_name != "Eligibility":
        branch_Name+=branches[branch_name]+", "

current_job+=fdes+jdes+"\n"+branch_Name+"\n";

driver.back()
all_data += current_job + "---------------------------------\n\n"
# current_job+="djbvjief"
if previous_job == current_job:
  previous_job = current_job
else:
  previous_job = current_job
  jobmessage = "New Job Posted"+ "\n---------------------------------\n"
  scraped_data = jobmessage + current_job + "---------------------------------\n"
  for user_id in user_ids:
    update(user_id,scraped_data)
  if scraped_data is not None:
    bot.send_message(chat_id="@rmnotices", text=scraped_data)

# print("all_data", all_data)
# print("scraped_data", scraped_data)
print(user_ids)
# Close the browser
# scraped_data="hfuyfuky"
driver.quit()


# Function to schedule the scraping task
# def task_function():
#     global user_ids;
#     while True:
#         # Call the task function
#         jobs_updates()
#         # Wait for 60 seconds before running the task again
#         time.sleep(60)

# # Create a new thread for running the task function
# task_thread = threading.Thread(target=task_function)
# task_thread.daemon = True  # Set the thread as a daemon thread

# # Start the task thread
# task_thread.start()

# Start the bot polling
bot.polling()

# The program will continue running here while the bot is polling and the task thread is running in the background
