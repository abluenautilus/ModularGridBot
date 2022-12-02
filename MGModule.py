from bs4 import BeautifulSoup
import requests
import re

url_main = "https://modulargrid.net"
max_results = 10


class MGModule:

    def __init__(self):
        self.vendor = ""  # name of vendor
        self.module_name = ""  # name of module
        self.module_slug = ""  # module slug
        self.price = 0  # module price in currency
        self.hp = 0  # module with in hp
        self.depth = 0  # module depth in mm
        self.v12 = 0  # current draw 12V
        self.v12n = 0  # current draw -12V
        self.v5 = 0  # current draw 5v
        self.currency = ""  # currency for price
        self.img_url = ""  # url for module image
        self.url = ""  # main url for module

    def initFromPage(self, response):
        soup = BeautifulSoup(response.content, "html.parser")

        self.url = response.url

        # Get image URL
        centered_module = soup.find("a", class_="centered-module")
        img_loc = centered_module['href']
        self.img_url = "%s/%s" % (url_main, img_loc)

        # Get module metadata
        self.module_name = centered_module.attrs['title']

        vendor = soup.find("div", class_="sub-header").find("span")
        if vendor:
            self.vendor = vendor.text
        else:
            self.vendor = ""

        module_and_vendor = soup.find("meta", property="og:title")["content"]
        self.module_slug = re.sub(" ", "-", module_and_vendor)

        # Get basic module info
        box_specs = soup.find("div", class_="box-specs")

        hp_text = box_specs.find("dd", string=lambda text: "HP" in text)
        if hp_text:
            hp_text = hp_text.text
            result = re.match("(\d*) HP", hp_text)
            if result:
                self.hp = result.groups()[0]
        else:
            self.hp = "??"

        # some modules don't list depth
        if "deep" not in box_specs.decode():
            self.depth = "??"
        else:
            depth_text = box_specs.find("dd", string=lambda text: "deep" in text)
            if depth_text:
                depth_text = depth_text.text
                result = re.match("^(\d*)", depth_text)
                if result:
                    self.depth = result.groups()[0]
            else:
                self.depth_text = "??"

        # current draw
        if "does not draw current" in box_specs.decode():
            self.v12 = "none"
            self.v12n = "none"
            self.v5 = "none"
        else:
            muted = box_specs.find_all("dd", class_="muted")
            if muted:
                mt = " ".join([elem.text for elem in muted])
            else:
                mt = ""
            if not "+12V" in mt:
                V12_text = box_specs.find("dd", string=lambda text: "+12V" in text)
                if V12_text:
                    V12_text = V12_text.text
                    result = re.match("^(\d*)", V12_text)
                    if result:
                        self.v12 = result.groups()[0]
                else:
                    self.v12 = "??"
            else:
                self.v12 = "??"

            if not "-12V" in mt:
                V12N_text = box_specs.find("dd", string=lambda text: "-12V" in text)
                if V12N_text:
                    V12N_text = V12N_text.text
                    result = re.match("^(\d*)", V12N_text)
                    if result:
                        self.v12n = result.groups()[0]
                else:
                    self.v12n = "??"
            else:
                self.v12n = "??"

            if not "5V" in mt:
                V5_text = box_specs.find("dd", string=lambda text: "5V" in text)
                if V5_text:
                    V5_text = V5_text.text
                    result = re.match("^(\d*)", V5_text)
                    if result:
                        self.v5 = result.groups()[0]
            else:
                self.v5 = "??"

        price = soup.find("span", class_="currency")

        if not price:
            price = soup.find("span", class_="currency-approx")

        if price:
            price = price.text
            result = re.match("≈?[\$€](\d*)", price)
            if result:
                self.price = result.groups()[0]
            result = re.match("≈?([\$€])\d*", price)
            if result:
                self.currency = result.groups()[0]
        else:
            self.price = "unknown"

    async def render(self, message, bot_message):

        # print module info out to the channel
        await message.channel.send("**%s %s**" % (self.vendor, self.module_name))
        await message.channel.send(self.img_url)
        await message.channel.send("```css\n%s HP\n%s mm deep\nCurrent draw: %s/%s/%s mA\nPrice: %s%s```" % (
            self.hp, self.depth, self.v12, self.v12n, self.v5, self.currency, self.price))
        await message.channel.send("<%s>" % self.url)

    async def search(self, searchterm, message, bot_message, num_alternates):

        # Search for module info on MG
        # Uses GET request

        num_alternates = int(num_alternates)
        search_url = "%s/e/modules/find" % (url_main)
        data = {'SearchName': searchterm,
                'SearchVendor': '-',
                'SearchFunction': '-',
                'SearchSecondaryfunction': '-',
                'SearchHeight': 'All',
                'SearchTe': '',
                'SearchTemethod': 'max',
                'SearchBuildtype': 'All',
                'SearchLifecycle': '-',
                'SearchSet': 'all',
                'SearchMarketplace': '-',
                'SearchIsmodeled': '0',
                'SearchShowothers': '1',
                'order': "popular",
                'direction': "asc"
                }

        search_result = requests.get(search_url, params=data)
        if search_result.status_code == 200:
            soup = BeautifulSoup(search_result.content, "html.parser")
            box_modules = soup.find_all("div", class_="box-module")
            num_found = len(box_modules)

            if num_found == 0:
                await message.channel.send("No results found, sorry.")
            elif num_found == 1:
                await bot_message.edit(content="Found one single result, will load...")

                url = box_modules[0].find("a", class_="finder-thumb add-module")
                if url:
                    urlstem = url["href"]
                    url = "%s/%s" % (url_main, urlstem)
                # Fetch URL

                response = requests.get(url)

                # Show the single result
                self.initFromPage(response)
                await self.render(message, bot_message)
            else:

                await message.channel.send("%d results, showing most popular" % (num_found))
                main_result = box_modules[0]
                module_name = main_result.find(class_="module-name")
                if module_name:
                    module_name = module_name.text
                vendor = main_result.find("h4", class_="module-name")
                if vendor:
                    vendor = vendor.find("a")
                    if vendor:
                        vendor = vendor.text
                url = main_result.find("a", class_="finder-thumb add-module")
                if url:
                    urlstem = url["href"]
                    url = "%s%s" % (url_main, urlstem)

                    url_to_load = url
                    response = requests.get(url_to_load)
                    self.initFromPage(response)
                    await self.render(message, bot_message)

            # Display list of alternate results
            if num_alternates > 0 and num_found > 0:
                await message.channel.send("Other results:")

                for result_count in range(1, min(num_alternates, num_found)):
                    result = box_modules[result_count]
                    url_to_load = ""

                    if result_count <= max_results:
                        module_name = result.find(class_="module-name")
                        if module_name:
                            module_name = module_name.text
                        vendor = result.find("h4", class_="module-name")
                        if vendor:
                            vendor = vendor.find("a")
                            if vendor:
                                vendor = vendor.text
                        url = result.find("a", class_="finder-thumb add-module")
                        if url:
                            urlstem = url["href"]
                            url = "%s%s" % (url_main, urlstem)

                        await message.channel.send("%d: %s %s <%s>" % (result_count + 1, vendor, module_name, url))

        else:
            await message.channel.send("Error searching for module.")
