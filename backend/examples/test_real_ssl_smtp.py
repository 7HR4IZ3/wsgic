from cork import Cork

import logging

logging.basicConfig(format='localhost - - [%(asctime)s] %(message)s', level=logging.DEBUG)
log = logging.getLogger(__name__)

aaa = Cork('example_conf',
    email_sender='federico.ceratto@gmail.com',
    smtp_url='ssl://federico.ceratto@gmail.com:jckgtwesxgfrrqfi@smtp.gmail.com:587'
)

aaa.register('user', 'pass', 'federico.ceratto@gmail.com')
