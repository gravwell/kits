# Contributing

This file documents some important considerations when making contributions to the kits repository.

## Importing / Updating Kits

To bring a new kit into the repository, first build & download the kit using the Gravwell web UI, then create a new subdirectory for the kit and use [kitctl](https://www.gravwell.io/blog/get-your-kits-into-git-with-kitctl) to unpack the kit:

```
mkdir my-new-kit && cd my-new-kit
kitctl unpack ~/Downloads/my-new-kit.kit
```

This will expand the kit into git-friendly files.

Updating a kit works similarly. First, use the Gravwell web UI to modify whichever items you intend to change, then build a new kit containing just those modified items -- you should be able to put in simple placeholders for everything else (kit name, ID, description, banner image, etc.). Then use kitctl to *import* the contents of that kit file:

```
cd my-new-kit
kitctl import ~/Downloads/my-new-kit-v2.kit
```

## Resources

When packaging external resources, ensure any relevant licenses are included in the manifest. Refer to the `pihole` kit to see how licenses can be included in a kit.

## Images/Screenshots

Any images or screenshots included in the kit, whether as part of the icon/cover/banner imagery for the kit or packaged in a playbook, must be either created by the kit author *or* appropriately licensed and attributed.

## Automations

If your kit includes automations, they will all be closely scrutinized during the review process and may delay the acceptance of your PR.

Automations must not send data to any external systems, interact with admin APIs, or attempt to modify the permissions of any Gravwell components.

If your automation retrieves data from e.g. an external REST API, make sure to use config macros or secrets to allow a user to install their own API key. Do not include your own API key!
