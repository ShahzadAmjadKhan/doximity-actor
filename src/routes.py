from crawlee.beautifulsoup_crawler import BeautifulSoupCrawlingContext
from crawlee.router import Router
from crawlee.storages._key_value_store import KeyValueStore

router = Router[BeautifulSoupCrawlingContext]()

@router.default_handler
async def default_handler(context: BeautifulSoupCrawlingContext) -> None:
    # This is a fallback route which will handle the start URL.
    context.log.info(f'default_handler is processing {context.request.url}')
    keystore = await KeyValueStore.open(name='actor-input')
    input = await keystore.get_value(key='input')
    context.log.info(f'input is processing {input}')
    state = input.get('state')
    link = context.soup.find('a', string=state)
    href = link.get('href') if link else None

    if href:
        await context.enqueue_links(
            selector=f'a[href *="{href}"]',
            label="STATE")
    else:
        context.log.info(f'no state found {state}')

@router.handler('STATE')
async def state_handler(context: BeautifulSoupCrawlingContext) -> None:

    context.log.info(f'state_handler is processing {context.request.url}')
    context.log.info(f'state_handler is processing using proxy {context.proxy_info}')

    try:
        await context.enqueue_links(
            selector='li > a[href *="/directory/md/location/"]',
            label="CITY")

        next_button = context.soup.select(selector='a.next_page')

        if next_button:
            await context.enqueue_links(
                selector='a.next_page',
                label='STATE')
    except:
        context.log.exception(f'state_handler exception in processing {context.request.url}')
        context.log.info(f'http response status: {context.http_response.status_code}')
        context.log.info(f'http response body: {context.http_response.read()}')


@router.handler('CITY')
async def city_handler(context: BeautifulSoupCrawlingContext) -> None:
    context.log.info(f'city_handler is processing {context.request.url}')
    context.log.info(f'city_handler is processing using proxy {context.proxy_info}')
    try:
        await context.enqueue_links(
            selector='a[href *="/pub/"]',
            label="DOCTOR")

        next_button = context.soup.select(selector='a.next_page')
        if next_button:
            await context.enqueue_links(
                selector='a.next_page',
                label='CITY')
    except:
        context.log.exception(f'city_handler exception in processing {context.request.url}')
        context.log.info(f'http response status: {context.http_response.status_code}')
        context.log.info(f'http response body: {context.http_response.read()}')

@router.handler('DOCTOR')
async def doctor_handler(context: BeautifulSoupCrawlingContext) -> None:
    context.log.info(f'doctor_handler is processing {context.request.url}')
    context.log.info(f'doctor_handler is processing using proxy {context.proxy_info}')

    try:
        doctor_info = {}
        soup = context.soup
        first_name = soup.select('#user_full_name > span.user-name-first')
        if first_name:
            doctor_info['first_name'] = first_name[0].get_text(strip=True) if first_name else ''

        middle_name = soup.select('#user_full_name > span.user-name-middle')
        if middle_name:
            doctor_info['middle_name'] = middle_name[0].get_text(strip=True) if middle_name else ''

        last_name = soup.select('#user_full_name > span.user-name-last')
        if last_name:
            doctor_info['last_name'] = last_name[0].get_text(strip=True) if last_name else ''

        suffix = soup.select('#user_full_name > span.user-name-suffix')
        if suffix:
            doctor_info['suffix'] = suffix[0].get_text(strip=True) if suffix else ''

        credentials = soup.select('#user_full_name > span.user-name-credentials')
        if credentials:
            doctor_info['credentials'] = credentials[0].get_text(strip=True) if credentials else ''
        else:
            credentials = soup.select('#user_full_name > span.user-name-credentials-additional')
            if credentials:
                doctor_info['credentials'] = credentials[0].get_text(strip=True) if credentials else ''

        # Scrape speciality
        speciality_anchor = soup.select_one('.profile-head-subtitle')
        if speciality_anchor:
            doctor_info['speciality'] = speciality_anchor.get_text(strip=True)

        # Scrape contact information
        contact_info_section = soup.select_one('.profile-contact-information')
        if contact_info_section:
            office_address = contact_info_section.select_one('.profile-contact-information-office-line-item')
            doctor_info['office_address'] = office_address.get_text(strip=True) if office_address else ''
            phone_number = contact_info_section.select_one('.office-info-telephone')
            doctor_info['phone_number'] = phone_number.get_text(strip=True) if phone_number else ''
            fax_element = contact_info_section.select_one('.office-info-fax')
            doctor_info['fax_number'] = fax_element.get_text(strip=True) if fax_element else ''

        # Scrape summary
        summary_section = soup.select_one('.profile-summary-content')
        if summary_section:
            doctor_info['summary'] = summary_section.get_text(strip=True)

        # Scrape education and training info
        doctor_info['education_and_trainings'] = []
        education_lis = soup.select('.education-info li[itemprop="alumniOf"]')
        for li in education_lis:
            spans = li.select('div > span')
            education_info = ', '.join([span.get_text(strip=True) for span in spans])
            doctor_info['education_and_trainings'].append(education_info)

        # Scrape certification info
        doctor_info['certifications'] = []
        certification_lis = soup.select('.certification-info li.show_more_hidden')
        for li in certification_lis:
            spans = li.select('div > span')
            certification_info = ', '.join([span.get_text(strip=True) for span in spans])
            doctor_info['certifications'].append(certification_info)

        # Scrape license info
        doctor_info['licenses'] = []
        license_lis = soup.select('.certification-info li:not(.show_more_hidden)')
        for li in license_lis:
            spans = li.select('span')
            license_info = ', '.join([span.get_text(strip=True) for span in spans])
            doctor_info['licenses'].append(license_info)

        # Scrape award info
        doctor_info['awards'] = []
        award_lis = soup.select('.award-info li')
        for li in award_lis:
            spans = li.select('span')
            award_info = ', '.join([span.get_text(strip=True) for span in spans])
            doctor_info['awards'].append(award_info)

        # Scrape hospital info
        doctor_info['hospitals'] = []
        hospital_lis = soup.select('.hospital-info li[itemprop="affiliation"]')
        for li in hospital_lis:
            spans = li.select('div > span')
            hospital_info = ', '.join([span.get_text(strip=True) for span in spans])
            doctor_info['hospitals'].append(hospital_info)

        # Add state and city
        city = soup.select('#PostalAddress > span:nth-child(2) > a')
        if city:
            doctor_info['city'] = city[0].get_text(strip=True) if city else ''

        state = soup.select('#PostalAddress > span:nth-child(3) > a')
        if state:
            doctor_info['state'] = state[0].get_text(strip=True) if state else ''

        await context.push_data(doctor_info)
    except:
        context.log.exception(f'doctor_handler exception in processing {context.request.url}')
        context.log.info(f'http response status: {context.http_response.status_code}')
        context.log.info(f'http response body: {context.http_response.read()}')
