FROM node:20-alpine

WORKDIR /app

COPY ./frontend /app

RUN npm install

EXPOSE 3000

CMD ["npm", "run", "dev"]