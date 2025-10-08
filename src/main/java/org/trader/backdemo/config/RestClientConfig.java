package org.trader.backdemo.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.BufferingClientHttpRequestFactory;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;

@Configuration
public class RestClientConfig {

    @Bean
    public RestTemplate restTemplate() {
        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        requestFactory.setConnectTimeout(5000);
        requestFactory.setReadTimeout(10000);
        requestFactory.setBufferRequestBody(true);

        // Wrapper pour forcer le buffering complet
        BufferingClientHttpRequestFactory bufferingFactory =
                new BufferingClientHttpRequestFactory(requestFactory);

        return new RestTemplate(bufferingFactory);
    }
}
