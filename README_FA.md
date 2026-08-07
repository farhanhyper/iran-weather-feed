# GitHub Weather Feed برای بات TeamSpeak

این پوشه را داخل یک Repository عمومی GitHub قرار بده. GitHub Actions هر ۱۵ دقیقه آب‌وهوای ۳۱ استان را از Open-Meteo می‌گیرد و فایل `weather.json` را به‌روزرسانی می‌کند. VPS فقط `raw.githubusercontent.com` را می‌خواند.

## نصب

1. در GitHub یک Repository **Public** با نام پیشنهادی `iran-weather-feed` بساز.
2. محتویات همین پوشه را در **ریشه Repository** آپلود کن. پوشه مخفی `.github` هم باید آپلود شود.
3. وارد تب **Actions** شو و Workflow با نام `Update Iran weather JSON` را باز کن.
4. گزینه **Run workflow** را یک بار اجرا کن.
5. بعد از سبز شدن Workflow، فایل `weather.json` باید ۳۱ استان داشته باشد.
6. Raw URL فایل را به این شکل بساز:

   `https://raw.githubusercontent.com/USERNAME/iran-weather-feed/main/weather.json`

7. این URL را در `config.php` بات، بخش `WeatherIran > source_url` قرار بده.
8. روی VPS اجرا کن:

   `php weather_github_test.php`

   اگر `RESULT: OK` دیدی، بات را Restart کن:

   `./run stop`

   `./run start`

## نکته

اگر نام Repository یا Branch متفاوت است، `source_url` را مطابق همان تغییر بده. Repository باید Public باشد تا VPS بدون Token بتواند فایل Raw را بخواند.
