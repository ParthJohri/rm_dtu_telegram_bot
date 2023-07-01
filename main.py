import os
import threading
import re

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

collection = db['jobs']
last_document = db.jobs.find_one()  

print(last_document);
if last_document is None:
    previous_db = None
    previous_job = None
else:
    previous_db = last_document.get('previousdata')  
    previous_job = last_document.get('previousjob')  

        
user_ids = []

APIKEY = os.environ['API_KEY']
bot = telebot.TeleBot(APIKEY)

user_ids_dict = list(db.user.find({}, {"_id": 0, "userid": 1}))
user_ids = list(map(lambda item: item["userid"], user_ids_dict))

print("userids",user_ids)

channel_id = 'CHANNEL_ID'
@bot.message_handler(commands=['check'])

def send_message(message):
    rmmessage = "<b>RM Dashboard</b>\n"
    bot.send_message(message.chat.id, rmmessage, parse_mode="HTML")

@bot.message_handler(commands=['update'])
def update2(message):
  global user_ids
  user_ids_dict = list(db.user.find({}, {"_id": 0, "userid": 1}))
  user_ids = list(map(lambda item: item["userid"], user_ids_dict))
  user_id=message.chat.id
  if user_id in user_ids:
    bot.send_message(user_id, all_data, parse_mode="HTML")
  else:
    bot.reply_to(message, 'You have not granted permission.')

def update(user_id, data):
  global user_ids, all_data, scraped_data
  user_ids_dict = list(db.user.find({}, {"_id": 0, "userid": 1}))
  user_ids = list(map(lambda item: item["userid"], user_ids_dict))
  if user_id in user_ids:
          bot.send_message(user_id, data, parse_mode="HTML")


@bot.message_handler(commands=['permission'])
def ask_permission(message):
    global user_ids
    user_ids_dict = list(db.user.find({}, {"_id": 0, "userid": 1}))
    user_ids = list(map(lambda item: item["userid"], user_ids_dict))
    user_id = message.chat.id

    if user_id not in user_ids:
        bot.reply_to(message, 'Please enter your <b>DTU mail ID</b>:',parse_mode="HTML")
        
        bot.register_next_step_handler(message, process_mail_id)
    else:
        bot.reply_to(message, '<b>You have already granted permission.</b>', parse_mode="HTML")


def process_mail_id(message):
    user_id = message.chat.id
    mail_id = message.text.strip()
    reg= os.environ['REGEXP']
    if re.search(reg, mail_id):
        bot.reply_to(message, '<b>You have granted permission to receive automated messages.</b>', parse_mode="HTML")
        db.user.insert_one({"userid": user_id, "mailid": mail_id})
    else:
        bot.reply_to(message, '<b>Permission not granted. Please provide a valid DTU mail ID</b>', parse_mode="HTML")

@bot.message_handler(commands=['revoke'])
def revoke_permission(message):
  global user_ids
  user_ids_dict = list(db.user.find({}, {"_id": 0, "userid": 1}))
  user_ids = list(map(lambda item: item["userid"], user_ids_dict))
  user_id = message.chat.id
  if user_id in user_ids:
    bot.reply_to(message,
                 '<b>You have revoked permission to receive automated messages.</b>',parse_mode="HTML")
    db.user.delete_many({"userid":user_id})
  else:
    bot.reply_to(message, '<b>You have already revoked permission.</b>',parse_mode="HTML")


@bot.message_handler(commands=['start'])
def handle_start(message):
  # Prepare the list of commands
  commands = [
    '<b>/start -</b> To Start The Bot',
    '<b>/update -</b> To Update You About The Jobs',
    '<b>/permission -</b> Permitting the bot to send you messages after every hour',
    '<b>/revoke -</b> Revoke your permission', '/update - New Jobs/ Updates',
    '<b>/search -</b> Search for your Query'
  ]

  commands_text = '\n'.join(commands)

  bot.send_message(message.chat.id, f'<b>Available commands:</b>\n{commands_text}',parse_mode="HTML")


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
    bot.reply_to(message, "<b>Please enter your query</b>",parse_mode="HTML")
    bot.register_next_step_handler(message, process_query)

def process_query(message):
    query = message.text
    result = search(query)
    bot.reply_to(message, result)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    command = call.data

    if command == 'permission':
      bot.send_message(call.message.chat.id, "Permission")
      ask_permission(call.message)

    elif command == 'revoke':
      bot.send_message(call.message.chat.id, "Revoke")
      revoke_permission(call.message)

    elif command == 'update':
      bot.send_message(call.message.chat.id, "Update")
      update(call.message)

    elif command == 'search':
      bot.send_message(call.message.chat.id, "Search")
      search(call.message)

def scrape_function():
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome('/usr/local/bin/chromedriver',options=chrome_options)

    global scraped_data, previous_db, previous_job, all_data, user_ids, branches

    loginurl = ('https://rm.dtu.ac.in/api/auth/login')
    secure_url = ('https://www.rm.dtu.ac.in/app/dashboard')

    print(previous_db);
    print(previous_job);
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

    div_elements_first_three = div_elements[:3]

    all_data = "<b>🚀 RM Dashboard 📊</b>\n\n"
    # Iterate over the div elements and perform actions
    serial_number =1
    flag=True;
    for div in div_elements_first_three:
      # Perform actions on each div element
      companyname = div.find('p', class_='css-1v1tjum-MuiTypography-root').text
      companystatus = div.find_all('p', class_='css-ahj2mt-MuiTypography-root')
      # Print the name and status
      emoji_bullet = "🔹"  # Emoji bullet point
      nm = f"{emoji_bullet} <b>Name :</b> <i>{companyname}</i>\n\n"
      pt = ""
      serial_number += 1
      for p in companystatus:
        text = p.text.lstrip()  # Remove leading whitespaces
        emoji = ""
        detail = text
        if text.startswith("Name"):
            emoji = "✨ "
        elif text.startswith("Posted on"):
            emoji = "📅 "
        elif text.startswith("Deadline to Apply"):
            emoji = "⏰ "
        elif text.startswith("CutOff"):
            emoji = "🎓 "
        elif text.startswith("Stipend"):
            emoji = "💰 "
        elif text.startswith("Job Description"):
            emoji = "🌟 "
        elif text.startswith("Contact"):
            emoji = "📞 "
        elif text.startswith("Updated the job posted"):
            emoji = "🌟 "
        elif text.startswith("New job posted"):
            emoji = "📌 "
        if ':' in detail:
            split_str = detail.split(':', 1)
            first_part = split_str[0].strip() 
            second_part = split_str[1].strip()  
            finaldetail = f"<b>{first_part} :</b> <i>{second_part}</i>"
        else:
            print("Invalid input: No colon found in the string.")
            finaldetail = f"<i>{detail}</i>"
        pt += f"{emoji} {finaldetail}\n\n"
      
      temp=nm+pt;
      if(flag):
        current_db = nm + pt 
        flag=False;
      all_data += temp;
    if current_db == previous_db:
      previous_db = current_db
    else:
      previous_db = current_db
      rmmessage = "<b>🚀 RM Dashboard 📊</b>\n\n"
      scraped_data = rmmessage + current_db
      for user_id in user_ids:
        update(user_id,scraped_data)

    # Jobs Panel
    time.sleep(1)

    jobs = driver.find_element(By.XPATH, ".//a[@href='/app/jobs']")

    jobs.send_keys(Keys.ENTER)

    time.sleep(1)

    # Get the current URL
    current_url = driver.current_url

    page_jobs_source = driver.page_source

    soup = BeautifulSoup(page_jobs_source, 'html.parser')

    div_elements = soup.find_all('div', class_='css-wdtwov-MuiGrid-root')

    div_elements_first_three = div_elements[:3]
    latest_job = div_elements[0]
    rev_div_elements = div_elements_first_three[::-1]
    all_data += "-----------------------------------------------------------------\n\n"
    all_data += "<b>🔔 Jobs Updated 🔔</b>\n\n"
    # Iterate over the div elements and perform actions
    div=latest_job
    # for div in rev_div_elements:
    # Perform actions on each div element
    companyname = div.find('div', class_='css-dsnyvo')
    companystatus = div.find('div', class_='css-155ff3i')
    p_job_status = companystatus.find_all(
      'p', class_="css-ahj2mt-MuiTypography-root")
    nam = f"✨ <b>Name :</b> <i>{companyname.h5.text}</i>\n\n"

    # Print the name and status
    pt = ""
    for p in p_job_status:
      text = p.text.lstrip()  # Remove leading whitespaces
      emoji = ""
      detail = text
      
      if text.startswith("Name"):
          emoji = "✨ "
      elif text.startswith("Posted on"):
          emoji = "📅 "
      elif text.startswith("Deadline to Apply"):
          emoji = "⏰ "
      elif text.startswith("CutOff"):
          emoji = "🎓 "
      elif text.startswith("Stipend"):
          emoji = "💰 "
      elif text.startswith("Job Description"):
          emoji = "🌟 "
      elif text.startswith("Contact"):
          emoji = "📞 "
      elif text.startswith("Updated the job posted"):
          emoji = "🌟 "
      
      if ':' in detail:
            split_str = detail.split(':', 1)
            first_part = split_str[0].strip() 
            second_part = split_str[1].strip()  
            finaldetail = f"<b>{first_part} :</b> <i>{second_part}</i>"
      else:
            print("Invalid input: No colon found in the string.")
            finaldetail = f"<i>{detail}</i>"
      pt += f"{emoji} {finaldetail}\n\n"
    current_job = nam + pt
    
    print("Know More")
    KMore = driver.find_element(By.XPATH, '/html/body/div/div/div[3]/div/div/div/div[1]/div/div/div[2]/div/div[1]/div/div/div[2]/a[1]/button')
    KMore.send_keys(Keys.ENTER)
    time.sleep(5)
    current_url = driver.current_url
    print(current_url)

    page_jobs_source = driver.page_source
    soup = BeautifulSoup(page_jobs_source, 'html.parser')

    # Find all elements with the specified class
    p_elements = soup.find_all('p', class_='MuiTypography-root MuiTypography-body1 css-ahj2mt-MuiTypography-root')

    if len(p_elements) > 1:
        second_p_element = p_elements[1]
        form_link = second_p_element.find('a')['href'] if second_p_element.find('a') else "N/A"
    else:
        form_link = "N/A"

    fdes = "📝 <b>Form Link :</b> "+form_link +"\n\n"

    # Extract job description
    anchor_element = soup.find('a')
    link = anchor_element['href']
    job_description = soup.find('p', class_="MuiTypography-root MuiTypography-body1 css-z2eky3-MuiTypography-root").text
    jdes = "🌟 " + job_description + "\n\n"
    jdes = f"<b>{jdes.split(':', 1)[0].strip()} :</b> <i>{jdes.split(':', 1)[1].strip()}</i>\n\n" if ':' in jdes else jdes

    P12th = "🎓 " + p_elements[4].text + "\n\n"
    P12th = f"<b>{P12th.split(':', 1)[0].strip()} :</b> <i>{P12th.split(':', 1)[1].strip()}</i>\n\n" if ':' in P12th else P12th

    P10th = "🏫 " + p_elements[5].text + "\n\n"
    P10th = f"<b>{P10th.split(':', 1)[0].strip()} :</b> <i>{P10th.split(':', 1)[1].strip()}</i>\n\n" if ':' in P10th else P10th

    Backlogs = "📚 " + p_elements[6].text + "\n\n"
    Backlogs = f"<b>{Backlogs.split(':', 1)[0].strip()} :</b> <i>{Backlogs.split(':', 1)[1].strip()}</i>\n\n" if ':' in Backlogs else Backlogs


    wait = WebDriverWait(driver, 10)  # Set an appropriate waiting time
    element = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/div/div[3]/div/div/div/div[8]/table/tbody/tr[1]/td[2]/div/div/div/div")))

    element.send_keys(Keys.ENTER)

    ul_element = element.find_element(By.XPATH, "//ul[@class='MuiList-root MuiList-padding MuiMenu-list css-6hp17o-MuiList-root-MuiMenu-list']")

    li_elements = ul_element.find_elements(By.TAG_NAME, "li")

    current_job+=fdes+jdes +P12th +P10th +Backlogs;

    driver.back()
    all_data += current_job + "\n"
    # current_job+="djbvjief"
    if current_job == previous_job:
      previous_job = current_job
    else:
      previous_job = current_job
      jobmessage = f"<b>🔥 New Job Posted 🔥</b> \n\n" 
      scraped_data = jobmessage + current_job + "\n\n"
      for user_id in user_ids:
        update(user_id,scraped_data)
      if scraped_data is not None:
        bot.send_message(chat_id="@rmnotices", text=scraped_data)
        
    db.jobs.insert_one({
    "previousdata": current_db,
    "previousjob": current_job})
    print(current_db)
    print("\n")
    print(current_job)
    print(user_ids)
    driver.quit()

def task_function():
  global user_ids;
  while True:
      try:
        # Call the task function
        scrape_function()
        # Wait for 60 seconds before running the task again
        time.sleep(60)
      except Exception as e:
        print(e)
        time.sleep(5)
        continue

# Create a new thread for running the task function
task_thread = threading.Thread(target=task_function)
task_thread.daemon = True  # Set the thread as a daemon thread

# Start the task thread
task_thread.start()

# Start the bot polling
while True:
    try:
        bot.polling(non_stop=True, interval=0)
    except Exception as e:
        print(e)
        time.sleep(5)
        continue

# The program will continue running here while the bot is polling and the task thread is running in the background
