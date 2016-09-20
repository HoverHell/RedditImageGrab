"""module to parse deviantart page."""
from HTMLParser import HTMLParser


# Used to extract src from Deviantart URLs
class DeviantHTMLParser(HTMLParser):
    """
    Parses the DeviantArt Web page in search for a link to the main image on page.

    Attributes:
        IMAGE  - Direct link to image
    """

    def __init__(self):
        """init func."""
        self.reset()
        self.IMAGE = None

    # Handles HTML Elements eg <img src="//blank.jpg" class="picture"/> ->
    #      tag => "img", attrs => [("src", "//blank.jpg"), ("class", "picture")]
    def handle_starttag(self, tag, attrs):
        # Only interested in img when we dont have the url
        # first search for download button
        if tag == "a" and self.IMAGE is None:
            # filter the probably a-tag, or link-tag or download button
            # download link class content of from a-tag class
            download_link_class = 'dev-page-button dev-page-button-with-text dev-page-download'
            # use the same method like below
            for classAttr in attrs:
                if classAttr[0] == "class":
                    # Incase page doesnt have a download button
                    if download_link_class in classAttr[1]:
                        for srcAttr in attrs:
                            if srcAttr[0] == "href":
                                self.IMAGE = srcAttr[1]

        # if download button not found get original image
        elif (tag == "a" or tag == "img") and self.IMAGE is None:
            # Check attributes for class
            for classAttr in attrs:
                # Check class is dev-content-normal
                if classAttr[0] == "class":
                    # Incase page doesnt have a download button
                    if classAttr[1] == "dev-content-normal":
                        for srcAttr in attrs:
                            if srcAttr[0] == "src":
                                self.IMAGE = srcAttr[1]
                    else:
                        return


def process_deviant_url(url):
    """
    process deviantart url.

    Given a DeviantArt URL, determine if it's a direct link to an image, or
    a standard DeviantArt Page. If the latter, attempt to acquire Direct link.

    Returns:
        deviantart image url
    """
    # We have it! Dont worry
    if url.endswith('.jpg'):
        return [url]
    else:
        # Get Page and parse for image link
        response = request(url)
        filedata = response.read()
        parser = DeviantHTMLParser()
        try:
            parser.feed(filedata)
            if parser.IMAGE is not None:
                return [parser.IMAGE]
            return [url]
        # Exceptions thrown when non-ascii chars are found
        except UnicodeDecodeError:
            if parser.IMAGE is not None:
                return [parser.IMAGE]
            else:
                return[url]
    # Dont return None!
    return [url]
