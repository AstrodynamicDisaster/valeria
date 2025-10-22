import dotenv
import os

dotenv.load_dotenv()

WOLTERS_API_BASE_URL="https://a3api.wolterskluwer.es/Laboral/api"
AUTH_URL="https://login.wolterskluwer.eu/auth/core/connect/token"
SUBSCRIPTION_KEY=os.getenv("A3_SUBSCRIPTION_KEY", "")
CLIENT_ID=os.getenv("A3_CLIENT_ID", "")
CLIENT_SECRET=os.getenv("A3_CLIENT_SECRET", "")
REFRESH_TOKEN=os.getenv("A3_REFRESH_TOKEN", "")