import re


text = """
Library of Congress Control Number: 2014954664
ISBN: 978-1-119-01792-9
ISBN: 978-1-119-01793-6 (ePDF); ISBN: 978-1-119-01794-3 (ePub)
Manufactured in the United States of America
liable to prosecution under the respective Copyright Law.
ISBN-13 (pbk): 978-1-4302-6451-4
ISBN-13 (electronic): 978-1-4302-6452-1
Trademarked names, logos, an
Livery Place
35 Livery Street
Birmingham
B3 2PB, UK.
ISBN 978-1-83882-658-1
www.packt.com
"""


isbn_list = []
pattern1 = re.compile(r"(?i)ISBN(?:-13)?\D*(\d(?:\W*\d){12})", re.M)
pattern2 = re.compile(
    r"(?:ISBN(?:-13)?:? )?(?=[0-9]{13}$|(?=(?:[0-9]+[- ]){4})[- 0-9]"
    r"{17}$)97[89][- ]?[0-9]{1,5}[- ]?[0-9]+[- ]?[0-9]+[- ]?[0-9]",
    re.M,
)

patterns = (pattern1, pattern2)


for pattern in patterns:
    matches = pattern.findall(text)
    print(matches)
