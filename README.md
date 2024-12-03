Babel translations files

    pybabel extract . -o app/locale/base.pot -F babel-mapping.ini
    
    # init language
    pybabel init -l tk -i app/locale/base.pot -d app/locale
    pybabel init -l en -i app/locale/base.pot -d app/locale
    pybabel init -l ru -i app/locale/base.pot -d app/locale
    
    # update language
    pybabel update -l en -i app/locale/base.pot -d app/locale
    pybabel update -l ru -i app/locale/base.pot -d app/locale
    pybabel update -l tk -i app/locale/base.pot -d app/locale

    pybabel compile -d app/locale

Install linux packages:

    apt install libwebp-dev libmagic1
