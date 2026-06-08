FROM apify/actor-node-playwright-chrome:20

COPY package*.json ./

RUN npm --quiet set progress=false \
  && npm install --no-optional \
  && echo "Installed NPM packages:" \
  && npm list

COPY . ./

RUN npm run build \
  && npm prune --production

CMD npm start
