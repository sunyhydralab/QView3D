echo Installing dependencies for QView3D

:pipSetup
pip install -r requirements.txt 
goto flaskSetup

:flaskSetup
cd server
rmdir /s /q "migrations"
flask db init
flask db migrate
flask db upgrade
goto clientSetup

:clientSetup
cd ../client
npm install --save-dev
npm run build-only
goto finish

:finish
echo Finished installed dependencies!