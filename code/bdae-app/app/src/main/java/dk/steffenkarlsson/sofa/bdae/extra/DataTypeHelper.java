package dk.steffenkarlsson.sofa.bdae.extra;

import android.app.Activity;
import android.view.Display;

/**
 * Created by steffenkarlsson on 6/3/16.
 */
public class DataTypeHelper {

    public static String getHTML(Activity activity, String result, String dataType) {
        switch (dataType) {
            case "img":
                Display display = activity.getWindowManager().getDefaultDisplay();
                int width = display.getWidth();

                return "<!DOCTYPE html>" +
                        "<html>" +
                        "<body>" +
                        String.format("<img width=\"%d\" src=\"%s\" />", width, result) +
                        "</body>" +
                        "</html>";
        }
        return "";
    }
}
