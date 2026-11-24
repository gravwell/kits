# Okta logos in this kit

The kit's icon, cover and banner use Okta's logo. Okta owns that logo and its trademarks, and
using it is governed by Okta's terms, not by this kit's BSD license. Read this before changing the
images or reusing them anywhere else.

## Where the logo comes from

- **Source:** the Okta newsroom, section "Looking for media assets?", set **Logos &
  boilerplates**: <https://www.okta.com/newsroom/>
- **File used:** `Okta_Aura Lockup_White_RGB.png` (the aura mark plus the "okta" wordmark, white,
  transparent background, 2829×1260) from `logos-11062026.zip`, downloaded 2026-11-24.
- **Not used:** the black lockup and the Auth0 logos in the same zip. The set contains no
  standalone aura mark, no banner image and no boilerplate text.

## Terms of use

Downloading or using the media assets means accepting Okta's
[Terms of Use for Okta Content](https://www.okta.com/terms-of-use-for-okta-content/) (the version
checked is dated 3 June 2025; read the current one before shipping a change). In short:

- **No changes to the logo.** It may only be used as Okta provides it: no cropping, recolouring,
  stretching, redrawing, effects, or separating the mark from the wordmark.
- **No implied endorsement.** Using the logo in a way that suggests Okta sponsors or endorses a
  product needs Okta's express written permission. Get sign-off from whoever handles trademark use
  at Gravwell before publishing the kit with these images.
- **No harmful use.** Nothing that disparages Okta, is defamatory or obscene, or infringes
  anyone's rights; the user indemnifies Okta.
- **Okta can withdraw permission** at its discretion. If it does, replace the images.
- **Questions** about trademark use go to <trademarks@okta.com>.

Okta publishes no clear-space, minimum-size or colour rules with this set; <https://brand.okta.com>
showed no guidelines when checked.

## How the kit's images were made

The logo file is scaled down as a whole, keeping its aspect ratio and the clear space built into
the PNG, and centred on a solid background in the kit's purple (`#2B1A3E`). Nothing in the logo
itself is changed.

| Kit image | Size | Content |
|---|---|---|
| `okta-banner.png` (`file/eabdba74-….contents`) | 765×300 | lockup scaled to 674×300, centred |
| `okta-cover.png` (`file/d96f0592-….contents`) | 300×300 | lockup scaled to 300×134, centred |
| `okta-icon.png` (`file/c7cccc24-….contents`) | 300×300 | same image as the cover |

Each image is stored twice with identical bytes: the top-level PNG used by `okta.metadata`, and
the file item under `file/` that the MANIFEST references. Update both.

The icon reuses the cover because the set has no square aura mark, and cutting the mark out of
the lockup would modify the logo. If Okta provides an aura-only mark, it could replace the icon.

## Changing the images

1. Download the current **Logos & boilerplates** set from <https://www.okta.com/newsroom/> and
   re-read the terms.
2. Use a lockup file exactly as supplied. Only scale it uniformly and place it on a background.
3. Regenerate all three images at the sizes above and write each to both of its locations.
