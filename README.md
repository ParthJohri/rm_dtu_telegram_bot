# DTU RM Portal Bot

Welcome to the DTU RM Portal Bot! 🤖 This bot is designed to provide you with valuable information about companies visiting DTU's Recruitment Management (RM) Portal. Stay updated on upcoming company visits, job openings, internships, and more.

## Key Features

- **Search Companies**: Find detailed information about companies visiting the DTU RM Portal.
- **Upcoming Visits**: Stay informed about the schedule of upcoming company visits.
- **Notifications**: Receive timely notifications about new job opportunities and internships.
- **Company Details**: Access comprehensive profiles of companies, including background, industry, and contact information.
- **Website Integration**: Seamlessly navigate the DTU RM Portal website for more details.

## Getting Started

1. Type `/start` to begin interacting with the bot.
2. Use the `/help` command to explore the available commands in the dropdown menu.

## Updates and Notifications

To receive updates and notifications, follow these steps:

1. Give the `/permission` command to register for notifications.
2. Use the `/updates` command to access the latest resume dashboard and job postings.
3. Use the `/ask` command to get answers to your interview questions, such as "top interview questions".

Registered users will receive notifications for new job openings. If you wish to stop receiving notifications, use the `/revoke` command.

## Deployment on AWS EC2

The DTU RM Portal Bot is deployed on AWS EC2 to ensure seamless availability and reliable performance. The EC2 instance provides a scalable and secure environment for hosting the bot.

## Flow Diagram

Below is a flow diagram illustrating the interaction and functionality of the DTU RM Portal Bot:

Flow Diagram Description:

Scrapping with Selenium: The flow begins with the Selenium script executing web scraping tasks. Selenium interacts with the target website, retrieves data, and performs necessary actions such as clicking buttons, filling forms, or extracting information.

Data Processing: Once the scraping is complete, the scraped data is processed and formatted according to your requirements. This may involve cleaning the data, extracting relevant information, or organizing it into a structured format.

Prompt on Telegram: The processed data is then used to generate a prompt or message that needs to be sent on Telegram. The message can contain the scraped information or any other relevant details you want to share with users.

Telegram Bot Interaction: The Telegram bot, deployed on AWS EC2, receives the prompt or message generated in the previous step. The bot handles incoming requests and messages from users.

AWS EC2 Deployment: The Telegram bot application is hosted and deployed on an AWS EC2 instance. EC2 provides a scalable and secure environment for running applications in the cloud. It ensures reliable availability and performance of the bot.

User Interaction: Users on Telegram can interact with the bot by sending messages, commands, or requests. They can trigger specific actions or ask for information using predefined commands or natural language queries.

Bot Response: The Telegram bot processes user requests, performs any necessary operations or calculations, and generates appropriate responses. In the context of your scenario, the bot may respond with the scraped data, additional information, or perform specific actions based on user commands.



## Feedback and Support

If you have any feedback, suggestions, or need assistance, please feel free to reach out to the bot administrator. We are dedicated to improving your experience and making the DTU RM Portal Bot even better!

Stay connected, stay informed, and make the most of the opportunities available through the DTU RM Portal Bot! 💼🌟
