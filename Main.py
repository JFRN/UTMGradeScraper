from libsrc.Scraper import GradeScraper
import time
start_time = time.time()


SCRAPER = GradeScraper('enrollment', 'password')

print(SCRAPER.averages_as_string('201740', True))
print(SCRAPER.subjects_details_as_string('201740'))

print("El programa se tardo {0} segundos".format(time.time() - start_time))