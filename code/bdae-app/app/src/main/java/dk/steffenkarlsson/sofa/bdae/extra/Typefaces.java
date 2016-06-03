package dk.steffenkarlsson.sofa.bdae.extra;

import android.content.Context;
import android.graphics.Typeface;

public class Typefaces {

    public static final int REGULAR = 0;
    public static final int LIGHT = 1;
    public static final int MEDIUM = 2;
    public static final int BOLD = 3;
    public static final int BLACK = 4;

    public Typeface get(Context c, int fontType) {
        String fontName = getFontName(fontType);
        try {
            return Typeface.createFromAsset(c.getAssets(), fontName);
        } catch (Exception e) {
            return null;
        }
    }

    private String getFontName(int fontType) {
        switch (fontType) {
            case LIGHT:
                return "Roboto-Light.ttf";
            case MEDIUM:
                return "Roboto-Medium.ttf";
            case BOLD:
                return "Roboto-Bold.ttf";
            case BLACK:
                return "Roboto-Black.ttf";
            case REGULAR:
            default:
                return "Roboto-Regular.ttf";
        }
    }

    private static Typefaces _instance = new Typefaces();

    public static Typefaces getInstance() {
        return _instance;
    }
}

