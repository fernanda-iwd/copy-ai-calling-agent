## Create a cloudflared tunnel

- Run this in one terminal to create an https tunnel

`cloudflared tunnel --url localhost:5000` (requires cloudflared to be installed: `brew install cloudflared`)

This tunnel will expire every few hours so you will need to run this again to obtain a new https tunnel

## Set up the project

You only need to do this once

- Start inside the `api` folder

- Create a python virtual environment

`python3 -m venv .venv`

- Add these env vars at the end of `.venv/bin/activate`:

```
  export BLAND_API_KEY={KEY}
  export LOCAL_URL={CLOUDFLARE_TUNNEL_URL}
  export INBOUND_PHONE_NUMBER={PHONE_NUMBER}
  export AZURE_OPENAI_API_KEY={KEY}
  export AZURE_OPENAI_ENDPOINT={ENDPOINT}
  export AZURE_DEPLOYMENT_NAME={NAME}
```

## Run the server

- Start inside the `api` folder

- Activate the environment

`. .venv/bin/activate`

- Install dependencies

`pip3 install -r requirements.txt`

- Run the server:

`flask --app src/app run`

## Run tests

- Start inside the `api` folder

- Activate the environment

`. .venv/bin/activate`

- Install dependencies

`pip3 install -r requirements.txt`


- **Run all tests**

  - Go inside the test directory, `cd test`
  - Then run, `python test_ai_agent.py`

- **Run a specific test**

  - While inside the `test` directory
  - Run, `python -m unittest test_ai_agent.TestAIAgent.{function_name}`
  - Example: `python -m unittest test_ai_agent.TestAIAgent.test_tc001` will run TC001 only
