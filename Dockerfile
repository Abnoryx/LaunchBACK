FROM apify/actor-node-playwright-chrome:20

COPY package*.json ./

RUN npm --quiet set progress=false \
  && npm install --only=prod --no-optional \
  && echo "Installed NPM packages:" \
  && npm list

COPY . ./

RUN npm run build

CMD npm start
