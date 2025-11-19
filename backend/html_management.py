from bs4 import BeautifulSoup


def format_image_srcs(html_content, base_url):
    print("html: ", html_content)
    soup = BeautifulSoup(html_content, 'html.parser')
    for img in soup.find_all('img'):
        src = img.get('src', '')
        if src and not src.startswith(('http://', 'https://', 'data:')):
            img['src'] = f'{base_url}/{src}'
    return str(soup).encode('utf-8')