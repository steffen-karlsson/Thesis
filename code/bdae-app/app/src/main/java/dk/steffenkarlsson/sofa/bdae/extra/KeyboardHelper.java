package dk.steffenkarlsson.sofa.bdae.extra;

import android.content.Context;
import android.view.View;
import android.view.inputmethod.InputMethodManager;

/**
 * Created by steffenkarlsson on 6/5/16.
 */
public class KeyboardHelper {

    public static void showKeyboardForView(Context context, View view) {
        view.requestFocus();
        InputMethodManager imm = (InputMethodManager) context.getSystemService(Context.INPUT_METHOD_SERVICE);
        imm.showSoftInput(view, InputMethodManager.SHOW_IMPLICIT);
    }
}
