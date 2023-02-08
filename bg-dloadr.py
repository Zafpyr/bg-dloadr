import sys, getopt, requests, re
from os import mkdir, path
from time import sleep
from bs4 import BeautifulSoup as Bs
from easysettings import load_json_settings
from colorama import init, Fore, Back, Style

# Initializes Colorama
init(autoreset=True)

history = load_json_settings('history.json')
history.save()

usage = 'USAGE: hdwallpapers.in_downloader.py --res=1920x1080,1280x1024,1440x900 --tag=anime --query="Dota"'
try:
    options, args = getopt.getopt(sys.argv[1:], 'hr:tq:cs', ['resolution=', 'tag=', 'query=', 'category=', 'path=',
                                                'dir=', 'per-res-dirs', 'disable-stealth', 'disable-headers'])
except getopt.GetoptError:
    print(usage)
    sys.exit(2)


print(options)
print(args)
site = 'https://www.hdwallpapers.in'
dl_dir = 'wallpapers'
stealth = True
disable_headers = False
per_res_dirs = False
resolution = ''
query = None
tag = None
category = None
opts = {}
for opt, arg in options:
    if opt == '-h':
        print(usage)
        sys.exit()
    elif opt in ("-r", "--resolution"):
        if ',' in arg:
            arg = arg.split(',', 10)
        resolution = arg
    elif opt in ("-t", "--tag"):
        if ',' in arg:
            arg = arg.split(',', 1000)
        tag = arg
        opts['tag'] = arg
    elif opt in ("-q", "--query"):
        if ',' in arg:
            arg = arg.split(',', 1000)
        query = arg
        opts['query'] = arg
    elif opt in ("-c", "--category"):
        if ',' in arg:
            arg.split(',', 35)
        category = arg
    elif opt in ("-p", "--path"):
        if ',' in arg:
            arg.split(',', 1000)
        arg = arg
        opts['path'] = path
    elif opt in ("-d", "--dir"):
        dl_dir = arg
    elif opt in ("-s", "--disable-stealth"):
        stealth = False
    elif opt in ("-a", "--disable-headers"):
        disable_headers = True
    elif opt in ("-e", "--per-res-dirs"):
        per_res_dirs = True


tags = []
if not dl_dir:
    dl_dir = 'wallpapers'


if not resolution:
    import tkinter
    root = tkinter.Tk()
    w = root.winfo_screenwidth()
    h = root.winfo_screenheight()
    resolution = str(w) + 'x' + str(h)
    print('A resolution was not specified, so using the detected resolution of ' + resolution)

def get_query_url(query):
    return f"{site}/search.html?q={opts['query']}"
def get_tag_url(tag):
    return f"{site}/tag/{opts['tag']}.html"
def get_category_url(category):
    return f"{site}/{opts['category']}-desktop-wallpapers.html"

def get_url():
    urls = []
    c=0
    no_spaces = Style.BRIGHT + Fore.RED + f'Error: Spaces are not allowed in tags!'
    prefixs = "search.html?q=", "tag/",  '',                        ''
    suffixs = '',               ".html", "-desktop-wallpapers.html" ""
    def build_url(c, method):
        if ('%20' in method or ' ' in method) and prefixs[c] == 'tag/':
            print(no_spaces + ' ' + method)
            return
        u = f"{site}/{prefixs[c]}{method}{suffixs[c]}"
        print(u)
        urls.append(u)
    print(opts)
    for m in ['query',          'tag',   'category',                'path']:
        try:
            method = opts[m]
            print('c '+str(c))
            if type(method) is str:
                build_url(c, method)
            else:
                for i in method:
                    print('item ' + i)
                    build_url(c, i)
        except:
            pass
        c = c + 1
    print(urls)
    return urls


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 '
                  'Safari/537.36',
    'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
    'referer': 'https://www.hdwallpapers.in/'
}


def get_html(URL, retry=0):
    parsed_html = False
    site_error = False
    if disable_headers:
        html = requests.get(URL)
    else:
        html = requests.get(URL, headers=headers)

    if Bs(html.content, 'html.parser'):
        parsed_html = Bs(html.content, 'html.parser')
    try:
        site_error = parsed_html.find('span', class_='errors').getText()
    except AttributeError:
        pass
    if html.ok and parsed_html and not site_error:
        return parsed_html
    else:
        if not html.reason:
            html.reason = 'Unknown'
        if site_error:
            print(Style.BRIGHT + Fore.RED + f'Error: {site_error}')
            return
        elif html.status_code == 404:
            print(Style.BRIGHT + Fore.RED + f'status: {html.status_code} Reason: {html.reason}'
                                            f'URL: {URL}')
            return
        elif 527 >= html.status_code and retry < 5:
            sleep(5)
            print(Style.BRIGHT + Fore.RED + f'status: {html.status_code} Reason: {html.reason} Retry: {retry}/{5} '
                                            f'URL: {URL}')
            retry = retry + 1
            return get_html(URL, retry)
        else:
            print(Style.BRIGHT + Fore.RED + 'Unknown error! Please report this to the developer.')
            print(Style.BRIGHT + Fore.RED + 'Reason: ' + html.reason)
            print(Style.BRIGHT + Fore.RED + 'status: ' + str(html.status_code))
            print(Style.BRIGHT + Fore.RED + ' ' + str(html.ok))
        return


def hist_add(k, v=None):
    if v and k in  history:
        if v not in history[k]:
            history[k].append(v)
            return True
    else:
        history[k] = []
        return True
    return False


def path_to_id(path):
    return path.replace('-wallpapers.html', '').replace('/', '')


def get_avail_res(path):
    results = {}
    id = path_to_id(path)

    if not stealth:
        for res in resolution:
            if hist_add(id, res):
                results[res] = f'download/{id}-{res}.jpg'
            else:
                print(Style.DIM + Fore.LIGHTYELLOW_EX + f'Skipped {id}-{res}.jpg, is in database. **')
        return results

    html = get_html(site + path)
    if html:
        resolution_links = html.find('div', class_='wallpaper-resolutions').findAll('a', href=True)
        for res in resolution_links:
            res_txt = res.getText().replace(' x ', 'x')
            if (type(resolution) is str and res_txt is resolution) or res_txt in resolution:
                if hist_add(id, res_txt):
                    results[res_txt] = res['href']
                else:
                    print(Style.DIM + Fore.LIGHTYELLOW_EX + f"Skipped {res['href']}, is in database. *")
        return results
    else:
        pass


def get_pagination(html):
    return html.find('div', class_='pagination')


def get_pagination2(html):
    pagination = html.find('div', class_='pagination')
    curpage = int(pagination.find('span', attrs={'class': 'selected'}).getText())
    page_btns = pagination.find_all('a')

    if page_btns:
        lastpage = int(page_btns[-2].getText())
    else:
        lastpage = 1

    if page_btns:
        page_btns = get_pagination(html).find_all('a')
    if page_btns[-1].getText().strip() == 'Next':
        nxt_page_path = f"{site}{page_btns[-1]['href']}"
        page_path = nxt_page_path
        URL = nxt_page_path

    results = {
        'curpage': curpage,
        'lastpage': lastpage,
        'page_btns': page_btns,
        'nxt_page_path': nxt_page_path,
        'page_path': page_path,
        'URL': URL
    }

    return results


linkst = {}


def get_links(url):
    links = []
    html = get_html(url)
    div = html.find('ul', class_='wallpapers')
    for a in div.findAll('a', href=True):
        link = a['href']
        if link:
            links.append(link)
    return links


def get_pages(url):
    pages = []
    html = get_html(url)
    if not html:
        return
    curpage = int(get_pagination(html).find('span', attrs={'class': 'selected'}).getText())
    page_btns = get_pagination(html).find_all('a')
    if page_btns:
        lastpage = int(page_btns[-2].getText())
    else:
        lastpage = 1
    page_path = ''
    while curpage <= lastpage:
        if not page_path:
            page_path = url
        print(f'page {curpage}/{lastpage}')

        pages.append(url)
        html = get_html(url)
        if page_btns:
            page_btns = get_pagination(html).find_all('a')
            if page_btns[-1].getText().strip() == 'Next':
                nxt_page_path = f"{site}{page_btns[-1]['href']}"
                page_path = nxt_page_path
                url = nxt_page_path
        curpage += 1
    return pages



def scrape_wallpapers():
    length = 0
    print(Style.DIM + Fore.BLUE + 'Scraping wallpaper query/tag/category results... ')
    pages = []
    results = []
    URL = get_url()
    wallpapers = []
    if type(URL) is str:
        print('URL: ' + URL)
        pages.extend(get_pages(URL))
    elif type(URL) is list:
        for u in URL:
            print('URL: '+u)
            pages.extend(get_pages(u))
    print(pages)
    for page in pages:
        print('page: '+page)
        wallpaper_paths = get_links(page)
        for w in wallpaper_paths:
            id = path_to_id(w)
            print('wp ' + id)
            resolutions = get_avail_res(w)
            if resolutions:
                results.append(resolutions)
                length += 1
    print(results)
    return results, length


def getFilename_fromCd(cd):
    """
    Get filename from content-disposition
    """
    if not cd:
        return None
    fname = re.findall('filename=(.+)', cd)
    if len(fname) == 0:
        return None
    return fname[0]


def download(url, subfolder: str = '', retry=0):
    url = f'{site}/{url}'
    result = {}
    r = ''
    print(url)
    if disable_headers:
        r = requests.get(url, allow_redirects=True)
    else:
        r = requests.get(url, allow_redirects=True, headers=headers)

    try:
        result['filename'] = getFilename_fromCd(r.headers.get('content-disposition'))
    except:
        return

    path_ = dl_dir

    if subfolder:
        path_ = path.join(dl_dir, subfolder)

    if not path.exists(path_):
        mkdir(path_)

    path_file = path.join(path_, result['filename'])
    result['ok'] = r.ok
    result['is_redirect'] = r.is_redirect
    result['status_code'] = r.status_code
    result['reason'] = r.reason
    result['request'] = r.request
    result['exists'] = True

    if r.ok:
        if not path.exists(path_file):
            open(path_file, 'wb').write(r.content)
            result['exists'] = False
        return result
    else:
        if not r.reason:
            r.reason = 'Unknown.'
        elif r.status_code == 404:
            print(Style.BRIGHT + Fore.RED + f'status: {r.status_code} Reason: {r.reason}'
                                            f'URL: {url}')
            return
        elif 527 >= r.status_code >= 400 and r < 5:
            sleep(5)
            print(Style.BRIGHT + Fore.RED + f'status: {r.status_code} Reason: {r.reason} Retry: {retry}/{5} '
                                            f'URL: {url}')
            retry = retry + 1
            return download(path, subfolder, retry)
        else:
            print(Style.BRIGHT + Fore.RED + 'Unknown error! Please report this to the developer.')
            print(Style.BRIGHT + Fore.RED + f'URL: {url}')
            print(Style.BRIGHT + Fore.RED + 'Reason: ' + r.reason)
            print(Style.BRIGHT + Fore.RED + 'status: ' + str(r.status_code))
            print(Style.BRIGHT + Fore.RED + ' ' + str(r.ok))
            return


def download_wallpapers():
    wallpapers, length = scrape_wallpapers()
    if len(wallpapers) <= 0:
        return

    c = 1
    print(Style.DIM + Fore.BLUE + f' Downloading wallpaper images..')
    for wallpaper in wallpapers:
        for res in wallpaper.keys():
            path = wallpaper[res]
            dl = download(path, res)
            filename = dl['filename']
            status = dl['status_code']
            if status == 200:
                if not dl['exists']:
                    print(Style.DIM + Fore.GREEN + f'{c}/{length}: {filename}')
                else:
                    print(Style.DIM + Fore.YELLOW + f'{c}/{length}: Skipped {filename}, already exists.')
            else:
                print(Style.BRIGHT + Fore.RED + f"{c}/{length}: Failed to download: {filename}."
                                                f" {dl['reason']}")
            c += 1


download_wallpapers()
history.save()


if linkst:
    print(linkst)
