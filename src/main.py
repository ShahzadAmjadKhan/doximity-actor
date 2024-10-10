import asyncio

from apify import Actor
from crawlee import ConcurrencySettings
from crawlee.beautifulsoup_crawler import BeautifulSoupCrawler
from crawlee.sessions import SessionPool
from crawlee.http_clients.curl_impersonate import CurlImpersonateHttpClient
from crawlee.memory_storage_client import MemoryStorageClient
from .routes import router

async def main() -> None:
    async with Actor:
        try:
            actor_input = await Actor.get_input() or {}
            keystore = await Actor.open_key_value_store(name='actor-input')
            await keystore.set_value('input', actor_input)
            sessionPool = SessionPool(max_pool_size=40)
            storage_client = MemoryStorageClient()
            await storage_client.purge_on_start()

            httpClient = CurlImpersonateHttpClient(
                timeout=10,
                impersonate='chrome124',
            )

            proxy = actor_input.get('proxy')
            proxy_configuration = None
            if proxy and proxy['useApifyProxy'] == True:
                proxy_urls = proxy.get('proxyUrls')
                if proxy_urls:
                    proxy_configuration = await Actor.create_proxy_configuration(proxy_urls=proxy_urls)
                else:
                    proxy_configuration = await Actor.create_proxy_configuration(
                        groups=proxy.get('apifyProxyGroups'),
                        country_code=proxy.get('apifyProxyCountry'))

                Actor.log.info(f"Using proxy configuraiton: {proxy_configuration}")

            settings = ConcurrencySettings(desired_concurrency=2)
            bs4_crawler = BeautifulSoupCrawler(
                proxy_configuration=proxy_configuration,
                concurrency_settings=settings,
                use_session_pool=True,
                session_pool=sessionPool,
                request_handler=router,
                http_client=httpClient,
                parser='html.parser')

            await bs4_crawler.run(['https://www.doximity.com/directory/md'])
        except:
            Actor.log.exception(f'exception in actor')

if __name__ == '__main__':
    asyncio.run(main())
