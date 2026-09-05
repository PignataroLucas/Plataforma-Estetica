module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react/recommended',
    'plugin:react/jsx-runtime',
    'plugin:react-hooks/recommended',
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs'],
  parser: '@typescript-eslint/parser',
  parserOptions: { ecmaVersion: 'latest', sourceType: 'module' },
  settings: { react: { version: '18.2' } },
  plugins: ['react-refresh', '@typescript-eslint'],
  rules: {
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true },
    ],
    'react/prop-types': 'off',
    '@typescript-eslint/no-explicit-any': 'warn',
    // El guion bajo adelante es la forma de decir "esto no se usa y es a
    // proposito": handlers que reciben un argumento que no les interesa,
    // desestructuraciones parciales. Sin esta regla el CI obliga a borrar
    // parametros que la firma necesita igual.
    '@typescript-eslint/no-unused-vars': [
      'error',
      {
        argsIgnorePattern: '^_',
        varsIgnorePattern: '^_',
        caughtErrorsIgnorePattern: '^_',
      },
    ],
    // `toISOString()` pasa a UTC antes de escribir la fecha, asi que recortarle
    // el 'YYYY-MM-DD' adelanta un dia a partir de las 21:00 en Argentina. Con
    // eso Mi Caja abria en la fecha de manana y los cobros de la noche se
    // guardaban con el dia equivocado. Mandar el instante completo sigue estando
    // bien; el problema es solo recortarlo.
    'no-restricted-syntax': [
      'error',
      {
        selector:
          "CallExpression[callee.object.callee.property.name='toISOString'][callee.property.name=/^(split|slice|substring|substr)$/]",
        message:
          'toISOString() pasa a UTC y adelanta el dia desde las 21:00 en Argentina. ' +
          'Usar getTodayForInput() o formatDateForInput() de utils/dateUtils.',
      },
    ],
  },
}
