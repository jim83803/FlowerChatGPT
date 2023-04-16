from dotenv import load_dotenv
from robot_controller import RobotController
import os

if __name__ == "__main__":
    load_dotenv()
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    robot_controller = RobotController('小花', DISCORD_TOKEN, OPENAI_API_KEY, 'gpt-3.5-turbo', 1.0, 4096, 2048)
    robot_controller.run()