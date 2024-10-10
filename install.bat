echo Installing dependencies for QView3D

:pipSetup
pip install -r requirements.txt 
goto flaskSetup

:flaskSetup
cd server
flask db init
flask db migrate
flask db upgrade
goto clientSetup

:clientSetup
cd ../client
npm install
npm run build-only
goto finish

:finish
echo Finished installed dependencies!