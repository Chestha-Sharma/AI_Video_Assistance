// Minimal cookie helper — no extra npm dependency needed.

const MAX_AGE_DAYS = 7

export function setCookie(name, value, days = MAX_AGE_DAYS) {
  try {
    const maxAge = days * 24 * 60 * 60
    const encoded = encodeURIComponent(value)
    document.cookie = `${name}=${encoded}; path=/; max-age=${maxAge}; SameSite=Lax`
  } catch (err) {
    console.error(`[cookies] failed to set "${name}":`, err)
  }
}

export function getCookie(name) {
  try {
    const match = document.cookie
      .split('; ')
      .find((row) => row.startsWith(`${name}=`))
    if (!match) return null
    return decodeURIComponent(match.split('=').slice(1).join('='))
  } catch (err) {
    console.error(`[cookies] failed to read "${name}":`, err)
    return null
  }
}

export function deleteCookie(name) {
  document.cookie = `${name}=; path=/; max-age=0; SameSite=Lax`
}
