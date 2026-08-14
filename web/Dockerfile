FROM node:20-alpine

ENV NODE_ENV=development

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .
RUN chown -R node:node /app

USER node
EXPOSE 5173

CMD ["npm", "run", "dev"]
