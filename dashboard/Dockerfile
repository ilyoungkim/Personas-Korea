FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . ./
RUN npm run build

FROM node:20-alpine

WORKDIR /app

COPY --from=build /app/.output ./.output
COPY --from=build /app/node_modules ./node_modules

ENV HOST=0.0.0.0 PORT=18080 NODE_ENV=production
EXPOSE 18080

CMD ["node", ".output/server/index.mjs"]
