```js
// ==UserScript==
// @name         Remove AutoTrader Ads
// @namespace    http://tampermonkey.net/
// @version      0.1
// @description  Remove ads on AutoTrader page
// @author       You
// @match        https://www.autotrader.co.uk/*
// @grant        none
// ==/UserScript==

(function() {
    // Wait for the page to fully load
    window.addEventListener('load', function() {
        console.log('start:');

        setTimeout(() => {
            // Select all elements that match the given data-testid values
            const adElements = document.querySelectorAll('[data-testid="FEATURED_LISTING"], [data-testid="YOU_MAY_ALSO_LIKE"], [data-testid="LEASING_LISTING"], [data-testid="PROMOTED_LISTING"]');

            // Iterate over each selected element and remove it
            adElements.forEach(function(adElement) {
                // Remove the parent element or the ad element itself
                if (adElement && adElement.parentElement) {
                    adElement.parentElement.parentElement.remove(); // Remove the parent of the ad
                }
            });

            console.log('End after 2 seconds');
        }, 1000);
    }, false);
})();
```

[[Tampermonkey]]
