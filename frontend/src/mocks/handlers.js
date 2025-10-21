import { rest } from 'msw';

export const handlers = [
  rest.get('/api/assets/defaults', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        us_equities: 50,
        intl_equities: 30,
        bonds: 20,
      })
    );
  }),
];