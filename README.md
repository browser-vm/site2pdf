# Site2PDF
A simple interactive Python script to download an entire website as a PDF.
![A simple graphic, basically a logo...](./images/site2-small.png)

## Codespace Setup
If you are on a Github Codespace, simply run ```setup.sh``` and you'll be good to go!

## Local Setup
1. First, clone the Git repo.
2. Then run ```sudo apt-get update -y``` to get fresh package lists.
3. Run ```pip install -r requirements.txt``` to install the Python deps.
4. Run ```playwright install chromium``` if you haven't already to install the browser Playwright will use.
5. Run ```sudo playwright install-deps``` if you haven't already to install the deps Playwright needs.
6. Run the script!

## Test
To make sure your link will work, you can run it through ```index_site.py``` first.